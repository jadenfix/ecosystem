# Beater × ReplayKit: one platform with deep replay

**Goal:** beater absorbs ReplayKit's full capability set — record → inspect → **fork → patch → replay-affected → diff** — so that beater is the single observe/replay/eval/gate platform, keeping the best design from each side. ReplayKit's ideas ship inside beater; ReplayKit the repo winds down to a feature-frozen reference once beater reaches parity.

This is written from a code audit of both repos (2026-07-05), not from their READMEs. File references below are real.

---

## 1. What each side does best

### beater keeps (already stronger)

| Capability | Where it lives | Why it wins |
| --- | --- | --- |
| Ingest | OTLP gRPC :4317 + OTLP/HTTP + native push (`POST /v1/traces/native`) + unified importer (`POST /v1/import/...` with pluggable `SourceImporter`s: native, temporal_history, Phoenix/LangSmith/Langfuse dialects) — `crates/beater-otlp`, `crates/beater-ingest` | ReplayKit has **zero** OTEL support; its collector (:4100) speaks a custom JSON span-lifecycle protocol only |
| Canonical schema | `CanonicalSpan` + `AgentSpanKind` (`crates/beater-schema/src/lib.rs`), versioned (`schema_version`, v1→v2 reprojection exists), semconv contract generated to `sdks/semconv/conventions.json` | ReplayKit's model is serde-JSON of unversioned structs with ad-hoc `u64` timestamps (ms in the collector, s elsewhere) |
| Artifacts & redaction | `ArtifactRef {artifact_id, uri, sha256, size_bytes, mime_type, redaction_class}` with `Public/Internal/Sensitive/Secret` classes; `SpanIoValue::Inline/Artifact/Redacted/Missing` read-back | ReplayKit has content-addressed blobs but no redaction model at all |
| Deterministic seams | `beater-replay` cassettes: `ReplayEvent {seq, kind, request_hash, response_hash}` over `Provider/Tool/Memory/Retrieval/Clock/Random`; `plan_replay`/`execute_replay`; **outcome-flip bisection** (`find_earliest_outcome_flip`, `attribute_failure`) | ReplayKit cannot replay `LlmCall` or `ToolCall` at all — LLM modes are `Blocked` (default), `Fake` (tests), `Passthrough` (**stub**) |
| Contract-first API | One OpenAPI contract (`sdks/openapi/beater-api.json`) generating 7 SDKs, CLI, MCP tools | ReplayKit's API is hand-rolled axum views |
| Downstream loop | Dataset promotion from traces, deterministic/judge evals, experiments, CI gates | ReplayKit has nothing past diff |

### ReplayKit contributes (the capabilities beater must gain)

| Capability | Where it lives | What beater lacks today |
| --- | --- | --- |
| **Explicit span-edge graph** | `SpanEdgeRecord` + `EdgeKind` (`ControlParent, DataDependsOn, RetryOf, Replaces, BranchOf, MaterializesSnapshot, ReadsArtifact, WritesArtifact`) — `crates/core-model/src/lib.rs` | beater has only `parent_span_id` + `seq`; no data-dependency edges, so no minimal re-run set |
| **Dirty-set replay planning** | `compute_dirty_map` in `crates/replay-engine/src/lib.rs`: patch a span → walk `DataDependsOn` for `UpstreamOutputChanged`, control-children as `DependencyUnknown`; only the dirty subgraph re-executes | beater's cassette replay re-runs linearly from a fork seq; no structural minimal re-run |
| **Typed patch taxonomy** | `PatchType`: `PromptEdit→LlmCall`, `ToolOutputOverride→ToolCall`, `ModelConfigEdit→LlmCall`, `RetrievalContextOverride→Retrieval`, `EnvVarOverride`, `SnapshotOverride`, with kind validation (`validate_patch_target`) | beater has no user-facing patch concept |
| **Per-span replay contract** | `ReplayPolicy` (`RecordOnly/RerunnableSupported/CacheableIfFingerprintMatches/PureReusable`), `input_fingerprint`/`output_fingerprint`, well-known attr keys (`command, cwd, path, content, provider, model, model_request_json`) | beater spans carry no replayability declaration or I/O fingerprints |
| **Real executors** | `CompositeExecutorRegistry`: `ShellCommand` (real `sh -c`, captures stdout/stderr/exit), `FileRead`, `FileWrite` (emits a diff artifact, never touches disk) | beater replays only recorded events; it executes nothing |
| **Branch/diff as first-class records** | `BranchRecord`, `ReplayJobRecord`, `RunDiffRecord`; one-call `POST /api/v1/branches` (fork+patch+replay), `/branches/plan` dry-run, cached run-vs-run diff, `/forensics` failure view | beater has no branch, no run diff, no forensics endpoint |

### The synthesis that makes the merge strictly better than either

ReplayKit's biggest hole is exactly what beater already has: it **blocks** `LlmCall`/`ToolCall` replay because it has no recorded provider events to substitute. Beater's cassette store *is* that substitute. Merged:

- Patched span → ReplayKit-style dirty-set walk finds the minimal re-run set.
- Dirty `llm.call`/`tool.call`/`memory.*`/`retrieval.query` spans whose `(seq, kind, request_hash)` still match the cassette are **satisfied deterministically from recorded events** — no live call, no `Blocked` status.
- Only spans whose *inputs actually changed* go live (or `Fake`, or stay blocked by policy).
- beater's outcome-flip bisection then runs *within the dirty subgraph* instead of the whole trace — faster attribution.

Neither system can do this alone today.

---

## 2. Target architecture (all inside beater)

### 2.1 Schema additions (`beater-schema`, semconv, OpenAPI — schema v3)

1. **`SpanEdge`** — new record: `{trace_id, from_span_id, to_span_id, kind}` with ReplayKit's `EdgeKind` verbatim. New table + `GET /v1/traces/{tenant}/{trace_id}/edges`.
2. **`CanonicalSpan` gains** `replay_policy: Option<ReplayPolicy>` (absent ⇒ `RecordOnly`), `input_fingerprint`/`output_fingerprint: Option<String>` (sha256 of canonical I/O bytes — beater already hashes artifacts, so this is cheap at ingest).
3. **Semconv keys** (via `xtask regen-semconv`, so every SDK inherits them):
   - `beater.replay.policy`
   - `beater.depends_on` (list of span ids → materialized as `DataDependsOn` edges at ingest)
   - replay-contract keys, namespaced: `beater.exec.command`, `beater.exec.cwd`, `beater.file.path`, `beater.file.content` (adopting ReplayKit's `attrs::*` contract under beater's namespace; `llm.provider`/`llm.model_name`/`model_request_json` already exist on the beater side).
4. **Span kinds:** do *not* grow `AgentSpanKind` with ReplayKit's `ShellCommand/FileRead/FileWrite/BrowserAction`. Map them to `tool.call` + a canonical attr `beater.tool.class ∈ {shell, file.read, file.write, browser}`. The ported executor registry dispatches on `(kind, beater.tool.class)` instead of kind alone. Keeps the kind enum small and the OTEL mapping stable.
5. **New records:** `Branch`, `Patch`, `ReplayJob`, `RunDiff` — ported from ReplayKit's `core-model` shapes, re-expressed in beater id/timestamp types, defined in the OpenAPI contract first (beater's [contract]-before-implementation discipline).

### 2.2 Engine (`beater-replay` grows into the replay engine)

Port from `ReplayKit/crates/replay-engine`:

- `plan_fork` / `compute_dirty_map` — unchanged logic; reads beater's span+edge tables. **No edges present (plain OTEL trace) ⇒ conservative control-parent dirtying** — exactly ReplayKit's existing fallback, so OTEL-only traces degrade gracefully rather than being unreplayable.
- `validate_patch_target` + patch disposition (`ToolOutputOverride` satisfies without re-exec; everything else re-runs the dirty set).
- Executor registry, with one change: **executor resolution order becomes cassette-first** —
  1. patched? → apply patch;
  2. cassette hit (`seq/kind/request_hash` match, input fingerprint unchanged)? → replay recorded response;
  3. executable (`shell`/`file.read`/`file.write` with satisfied attr contract)? → execute;
  4. else → `Blocked` with ReplayKit's `FailureClass::ReplayUnsupported` semantics.
- Keep beater's `SqliteReplayStore` cassettes as-is; branches/jobs/diffs go in the main store.
- Diff: port ReplayKit's run-vs-run diff into `GET /v1/traces/{tenant}/{a}/diff/{b}` with cached `RunDiff` records; wire outcome-flip attribution output into the diff view.

### 2.3 API (`beater-api`, port 8080 — ReplayKit's two-port split goes away)

New endpoints, contract-first so all 7 SDKs + MCP tools get them generated:

```
POST /v1/branches/{tenant}/{project}           # fork + patch + replay in one call
POST /v1/branches/{tenant}/{project}/plan      # dry-run: dirty set + per-span disposition
GET  /v1/replay-jobs/{tenant}/{job_id}
POST /v1/diffs/{tenant}                        # compute run-vs-run diff
GET  /v1/traces/{tenant}/{a}/diff/{b}          # cached
GET  /v1/traces/{tenant}/{trace_id}/edges
GET  /v1/traces/{tenant}/{trace_id}/forensics  # ReplayKit's failure-forensics view
```

Dashboard gains the fork/patch/diff/forensics UI (ReplayKit's web app is the design reference; the code is Vite-side and stays behind).

### 2.4 Loop closure (why absorption beats coexistence)

Once branches live inside beater, a **replayed branch is promotable**: fork a failing run, patch the prompt, replay the dirty set, diff — then promote the branch straight into a dataset case and gate the fix in CI. That end-to-end loop (`branch → diff → dataset → eval → gate`) is impossible across two databases, and it is the actual argument for beater having all of ReplayKit's capabilities rather than talking to them over a bridge forever.

### 2.5 Security boundary

Replaying a `shell` span is arbitrary code execution by construction. Rules:

- Executors run only with `--replay-exec` explicitly enabled on `beaterd`; default build ships cassette + fake + file-diff executors only.
- Spans with `redaction_class ∈ {Sensitive, Secret}` inputs are never live-replayed (cassette or blocked).
- Ecosystem option (consumer-gated, per the [ecosystem principles](https://github.com/jadenfix/ecosystem#design-principles)): route the shell executor through **beatbox** as the capability-scoped jail instead of raw `sh -c`. This lands only when the port reaches Phase C and a real deployment wants live shell replay.

---

## 3. Mapping reference (for the importer and the port)

| ReplayKit | beater | Note |
| --- | --- | --- |
| `RunRecord` | trace + `RunSummary` roll-up | `source_run_id`/`branch_id` → new `Branch` record |
| `SpanRecord.kind` `Run/PlannerStep` | `agent.run` / `agent.plan` | |
| `LlmCall/ToolCall/Retrieval` | `llm.call` / `tool.call` / `retrieval.query` | direct |
| `ShellCommand/FileRead/FileWrite/BrowserAction` | `tool.call` + `beater.tool.class` | see §2.1.4 |
| `MemoryLookup` | `memory.read` | |
| `HumanInput/GuardrailCheck` | `human.review` / `guardrail.check` | |
| `Subgraph/AdapterInternal` | `agent.step` + `beater.framework` | |
| `attrs::{command,cwd,path,content}` | `beater.exec.*` / `beater.file.*` | |
| `attrs::{provider,model,model_request_json}` | `llm.provider`, `llm.model_name`, `model_request_json` | already canonical in beater |
| artifact blobs (`blobs/sha256/...`) | `ArtifactRef` + artifact store | both content-addressed sha256 — hashes carry over unchanged |
| `EventRecord` | span events (beater OTLP events path) | |
| sequential ids (`run-0000…01`) | beater id newtypes | importer mints beater ids, keeps originals in `unmapped_attrs.replaykit.*` for provenance |
| `u64` timestamps (mixed ms/s) | `Timestamp` | importer normalizes; ms assumed for collector-written records |

---

## 4. Port plan (PR-sized, each phase independently shippable)

**Phase A — Contracts** (beater-schema + semconv + OpenAPI, no behavior):
`SpanEdge`, `ReplayPolicy`, fingerprints, `Branch/Patch/ReplayJob/RunDiff`, the new attr keys, endpoint stubs as [contract]. Schema v3 with a v2→v3 reprojection (the v1→v2 `reproject.rs` machinery is the template).

**Phase B — Bridge as parity oracle** (ships value immediately, de-risks the port):
`beaterctl export --format replaykit <trace_id>` — reads `getTrace` + `getSpanIo`, emits ReplayKit's collector lifecycle calls against :4100 (ReplayKit's §29 bundle import is unbuilt, so the live collector API *is* the import surface). This gives deep fork/patch/replay on real beater traces **before** the engine port lands, and produces the golden-run corpus: every behavior the bridge exercises becomes a parity test the port must match.

**Phase C — Engine port** (`beater-replay`):
dirty-set planner → cassette-first executor resolution → branches/jobs/diffs in the main store → API endpoints live → dashboard fork/patch/diff/forensics UI. Gate each PR on the Phase B golden runs (same patch on same trace ⇒ same dirty set, same dispositions, same diff).

**Phase D — Parity and wind-down**:
When the golden-run suite passes natively in beater: ReplayKit README points to beater as the successor, repo is feature-frozen (archived once no consumer remains), the bridge exporter is deleted (no dead glue), and the [ecosystem map](https://github.com/jadenfix/ecosystem) drops the ReplayKit node into beater's row.

Ordering rationale: A before B (the exporter needs the kind/attr mapping fixed in the contract), B before C (never port an engine without an oracle), D only on evidence. Each phase is useful if the next never happens — Phase B alone already delivers "deep replay for beater traces."

---

## 5. Risks and honest limits

- **Plain OTEL traces are only as replayable as what they captured.** No `input.value`/`output.value`/artifacts ⇒ `RecordOnly`; no `beater.depends_on` ⇒ conservative full-subtree re-run. The semconv additions make richness opt-in for instrumented SDKs; uninstrumented traces still get fork+diff, just with a bigger dirty set.
- **`FileWrite` replay hard-requires captured `content`** (ReplayKit rule, kept): the SDKs must artifact file contents at record time or those spans stay `RecordOnly`.
- **Two replay vocabularies during the transition.** `beater-replay`'s cassette types (`ReplayEvent`, `ReplayMode`) and the ported planner types coexist in one crate until Phase C unifies them behind the resolution order in §2.2 — name collisions (`ReplayMode` exists on both sides) must be resolved at port time, prefer the cassette names.
- **Fingerprint semantics must be pinned in Phase A**: sha256 over *canonical* serialized I/O (post-redaction, pre-compression), else cassette hits and dirty detection disagree across SDKs.
- **ReplayKit's `Passthrough`/live-LLM mode stays unimplemented** — deliberately. Live model calls during replay destroy determinism; the cassette + `Fake` + patch paths cover the real use cases. Revisit only with a concrete consumer.

---

## 6. Decision summary

| Dimension | Winner | Fate |
| --- | --- | --- |
| Ingest, schema, artifacts/redaction, API/SDK generation, datasets/evals/gates | **beater** | unchanged, becomes the host |
| Edge graph, dirty-set planning, patch taxonomy, replay policy, executors, branch/diff/forensics | **ReplayKit** | ported into `beater-schema` / `beater-replay` / `beater-api` |
| LLM/tool replay determinism | **beater cassettes** | becomes the executor fast path the port lacks today |
| Two-binary split (collector :4100 / API :3210) | neither | collapsed into `beaterd` |
| ReplayKit repo | — | parity oracle during the port; feature-frozen, then archived at Phase D |
