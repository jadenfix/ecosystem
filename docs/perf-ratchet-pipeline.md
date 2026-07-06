# The ratchet: metrics and a never-regress testing pipeline

**Goal:** every repo in the [ecosystem](../README.md) carries a committed performance baseline, CI blocks any change that makes a tracked metric worse than that baseline, and merged improvements automatically become the new baseline. The baseline only ever moves in the good direction — a one-way ratchet.

**The one design decision that makes this work:** metrics are split into two classes, because "must always be less than before" is only literally enforceable for one of them.

| Class | Examples | Gate | Tolerance |
| --- | --- | --- | --- |
| **Deterministic counters** — same input ⇒ same number, on any machine | bytes on the wire, allocations, executed instructions (cachegrind/iai), spans/queries per operation, tokens per observation, binary size, dependency count, unsafe/unwrap count | strict ratchet: `candidate ≤ baseline` | **zero** |
| **Stochastic timings** — wall-clock, throughput | p50/p99 latency, spans/sec ingest, time-to-finality | paired A/B vs baseline binary on the same machine in the same job, interleaved runs, median comparison | small (3–5%) + must also stay under an absolute budget |

Push everything you can into class 1. Most "performance" regressions (an extra serialization, a redundant clone, a chattier protocol, a bigger payload) show up perfectly in counters, which never flake. Wall-clock is the metric of last resort, not the default.

## 1. The metrics that matter (north stars per repo)

Each repo tracks 3–5 numbers that define its product promise. If one of these dips, the product got worse — everything else is diagnostic detail.

### beater (observe → replay → eval → gate)
| Metric | Class | Why it's the product |
| --- | --- | --- |
| Ingest cost per span (instructions + allocations, OTLP→stored) | counter | headroom for "point any agent at it" |
| Ingest throughput (spans/sec, sustained) and p99 ingest latency | timing | can't drop production traces |
| `getTrace` / span-tree read p99 at 10k-span traces | timing | the dashboard/debug loop |
| Bytes stored per canonical span (fixture corpus) | counter | storage economics |
| **Post-absorption:** dirty-set plan time per patched span; cassette hit rate on unchanged spans (must be 100% on golden runs); fork→diff wall time | counter + timing | the ReplayKit absorption promise |
| Gate correctness: false-pass = 0 on seeded-regression fixtures | counter | a gate that passes a regression is worse than no gate |

### tempo (agent-native browser)
| Metric | Class | Why |
| --- | --- | --- |
| Observation size (bytes and tokens) on the fixture page corpus | counter | the ~2–5KB thesis IS the product |
| Actions per task / round-trips per task on scripted flows | counter | batching thesis |
| Per-action p50/p99: observe → decide → act → settled (per lane, CDP and Servo) | timing | the measured bottleneck map lives here |
| ObservationDiff size on incremental steps | counter | diff-ability thesis |

### beater.js (durable polyglot runtime)
| Metric | Class | Why |
| --- | --- | --- |
| Journal overhead per step (bytes + fsync count + instructions) | counter | durability must stay cheap |
| Resume correctness: kill-9 matrix passes 100%; resume time after N-step run | counter + timing | the durability promise |
| Route p99 (V8) and SSR first-chunk time | timing | it's still a web server |
| Cold start of a built bundle | timing | the M8 deploy story |

### beatbox (capability sandbox)
| Metric | Class | Why |
| --- | --- | --- |
| Instantiate-to-first-instruction latency (hermetic module) | timing | sandbox tax = adoption blocker |
| Execution overhead vs native on fixture workloads | timing | same |
| Memory per idle job; job-store rows after retention run | counter | daemon must not grow |
| Escapes/capability leaks on the adversarial fixture suite | counter (= 0) | non-negotiable |

### beater-memory (typed temporal memory)
| Metric | Class | Why |
| --- | --- | --- |
| Query p99 per tier (lexical / graph / active reconstruction) | timing | read path is the product |
| Tokens returned vs budget (never over; utilization tracked) | counter | budget honesty |
| Provenance coverage of answers (= 100%) | counter | the differentiator |
| Distillation rejection rate on the malformed-provider corpus (all rejected, none looping) | counter | provider boundary |

### beaterOS (agent kernel)
| Metric | Class | Why |
| --- | --- | --- |
| Policy decision cost in **instructions** (it's a pure function — wall-clock is the wrong unit) | counter | hot-path kernel promise |
| Receipt write overhead per side effect | counter | audit must stay cheap |
| Decision replay determinism: byte-identical receipts on the conformance corpus (= 100%) | counter | the kernel promise itself |

### aether (L1)
| Metric | Class | Why |
| --- | --- | --- |
| Time-to-finality on the reference devnet topology (< 2s budget) | timing | the headline claim |
| TPS sustained on the standard mix; state-root compute time per block | timing | throughput claims |
| Cross-node determinism: identical state roots across N nodes on the replay corpus (= 100%) | counter | consensus survival |
| Block/vote validation cost in instructions | counter | adversarial headroom |

### Ecosystem-shared (every repo)
- Binary size of the shipped artifact(s).
- Full `cargo test` wall time and test count (suite time is a ratcheted metric too — slow suites rot).
- Dependency count (`cargo tree` unique crates) — justify-every-dependency, enforced.
- Clippy/`unsafe`/`unwrap` counts where the repo bans them (= 0, already gated).

## 2. Pipeline design

### 2.1 The baseline file (the ratchet's memory)

Each repo commits `perf/baseline.json`:

```json
{
  "schema": 1,
  "updated_by": "ratchet-bot after #576 @ abc1234",
  "metrics": {
    "ingest.instructions_per_span": { "class": "counter", "value": 41250, "direction": "down" },
    "observation.bytes.fixture_corpus_p95": { "class": "counter", "value": 4812, "direction": "down" },
    "ingest.p99_ms": { "class": "timing", "value": 8.4, "tolerance_pct": 4, "absolute_budget": 15.0 }
  }
}
```

Rules:
- The baseline is **committed**, so every ratchet movement is a visible diff with history and blame.
- `direction` makes "less than before" explicit per metric (some ratchet up, e.g. cassette hit rate, provenance coverage).
- An **absolute budget** accompanies every timing metric: the ratchet stops drift, the budget stops "we were always slow."

### 2.2 The PR gate (blocking)

One `perf-gate` CI job per repo:

1. **Counters:** run the instrumented fixture suite (fixed corpus, fixed seeds — inputs are part of the repo). Compare each counter to baseline. `candidate > baseline` (for direction=down) ⇒ **fail**, printing metric, baseline, candidate, delta, and the fixture that moved.
2. **Timings — paired A/B, never absolute:** the job builds BOTH the merge-base binary and the candidate binary, then runs them **interleaved** (A B A B …, ≥10 pairs after warmup) **on the same machine in the same job**. Compare paired medians. Fail if candidate is worse by more than `tolerance_pct` with sign-consistency across pairs (a Wilcoxon-style check; naive single-run comparison is banned). This kills machine drift, thermal state, and CI-runner lottery as false-failure sources — the enemy of a "never dips" rule is flake, because flaky gates get overridden and dead gates gate nothing.
3. Timings also check `absolute_budget` — a PR chain of nine 3% regressions can't ratchet you slowly past the budget line.
4. **Gate-honesty check (the reverted-fix test for perf):** the suite includes one intentionally-regressed fixture build (e.g. an env-var that adds a redundant serialization). If the gate does not fail on it, the gate itself is broken and the job fails. The pipeline proves it can catch a dip every time it runs.

### 2.3 The ratchet tightening (post-merge, automatic)

After every merge to the default branch:
- Re-run the suite on the merge commit (3 repetitions for timings).
- Any metric **better** than baseline beyond noise ⇒ ratchet-bot opens a one-line PR updating `perf/baseline.json` downward (auto-mergeable; non-author review rules still apply, so the bot PR is rubber-stampable by the owner in bulk).
- Metrics never loosen automatically. **The only way a baseline gets worse is a human editing `perf/baseline.json` in the same diff as the change that needs it**, with a `perf-tradeoff` label and a justification in the PR body. Silent regression is impossible; deliberate tradeoff is visible and reviewable. (This is the escape hatch — without one, the first genuinely-worth-it tradeoff, like adding auth to a hot path, forces people to game the suite instead.)

### 2.4 Hardware discipline (timings only)

- Timing jobs run on a **pinned self-hosted runner** (a dedicated always-on box — the Mac mini class of machine is fine), never on shared cloud runners.
- Warmup runs discarded; results recorded with machine fingerprint; if the runner changes, timings re-baseline from a clean sweep (counters are unaffected — that's why counters are the backbone).

### 2.5 Dogfood: beater is the metrics store and the gate

Every `perf-gate` run exports its results as OTEL spans to a beater instance (`evaluator.run` spans with metric attributes). That gives:
- history and dashboards for every metric per commit, for free;
- beater's own gate API (`POST /v1/gates/.../run`) as the eventual gate implementation — the ecosystem's CI-gate product gating the ecosystem;
- regressions promotable to datasets: a dip becomes a permanent fixture case (`from-trace`), so the corpus grows from real failures — the same failure can never sneak past twice.

Until beater's gate endpoints are fully live, a ~200-line `ratchet` script (read baseline, run suite, compare, exit code) in each repo does steps 2.2–2.3; the JSON format above is the contract so swapping the script for beater gates later changes nothing else.

## 3. What "never dips for anything" means precisely

1. **Counters never dip, period.** Zero tolerance, enforced on every PR, machine-independent.
2. **Timings never dip beyond noise**, verified by same-machine paired A/B — and never cross their absolute budget.
3. **Correctness ratchets are counters at 100%/0%:** determinism rates, provenance coverage, false-pass rate, escape count, kill-9 resume matrix. These are the metrics that are also promises; they sit in the same baseline file and the same gate.
4. **Every relaxation is a reviewed diff.** The baseline file is the single place regressions can be admitted, and it cannot change without a human-authored, labeled, justified PR.

## 4. Rollout order (consumer-gated, one PR-sized slice each)

1. **tempo** — it already has a measured bottleneck map and live perf PRs; codify existing numbers as the first `perf/baseline.json` + ratchet script. Highest immediate value.
2. **beater** — ingest + read-path counters and timings; then the absorption metrics (dirty-set plan cost, cassette hit rate) land as ratcheted metrics *from the first Phase C PR*, so deep replay is born gated and can never regress from its opening numbers.
3. **beatbox** — instantiation latency + adversarial-suite zero-escape counter.
4. **beater.js** — journal overhead + kill-9 matrix.
5. **beater-memory, beaterOS** — tier latencies / instruction-counted decisions as those hot paths stabilize.
6. **aether** — devnet finality/TPS harness is a bigger build; its determinism counter (identical state roots) should land first since it's cheap and existential.

Each rollout PR contains: the fixture corpus, the ratchet script wired into CI as a required check, the initial `baseline.json` measured on the pinned runner, and the gate-honesty fixture. Definition of done: a deliberately-added redundant serialization on a hot path fails CI in that repo.
