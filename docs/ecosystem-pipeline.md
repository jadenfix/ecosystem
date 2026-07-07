# Tempera Ecosystem Pipeline

The Tempera ecosystem root owns the pipeline. Product code stays in sibling
repos, but uniformity, release sync, and E2E capability gates are coordinated
here.

## Product Names

- Top coordination repo: `jadenfix/ecosystem`
- Palette: current repo `jadenfix/palette`
- temp.js: current repo `jadenfix/temp.js`
- tempo: current repo `jadenfix/tempo`
- tempOS: current repo `jadenfix/tempOS`
- remi: current repo `jadenfix/remi`
- cradle: current repo `jadenfix/cradle`
- Arrha: current repo `jadenfix/arrha`

## Subagent Direction

Subagents should treat this root as the source of truth. Start from
`jadenfix/ecosystem`, read `AGENTS.md`, `ecosystem.toml`,
`docs/architecture-uniformity.md`, and this file, then enter exactly one product
repo and work its local migration queue. The goal is modern, SOTA, uniform
engineering across the ecosystem, not repo-specific preference drift.

## Pipeline Shape

Run the pipeline in four stages:

1. `meta`: checks the root manifest, declared binaries, architecture policy, and
   repo/package metadata.
2. `repo`: runs each repo's own format, lint, test, package, and contract checks
   from `ecosystem.toml`.
3. `e2e`: runs capability scenarios across binaries and contract fixtures.
4. `release`: writes or verifies `ECOSYSTEM_RELEASE.toml` with repo SHAs,
   versions, toolchains, package managers, storage engines, and pass/fail status.
5. `watch`: monitors active open PRs across sibling repos and redirects coding
   agents back to ecosystem compatibility when needed.

During migration, run in `report` mode so agents get the full drift list without
stopping at the first failure. After the queues are done, CI should run the same
pipeline in `gate` mode and block drift.

If a repo already has an active PR, the next agent cycle on that PR should treat
pipeline compatibility as the first task. Do not expand unrelated feature scope
until the PR either moves the repo toward the uniform target or explicitly records
why a repo-local exception is still necessary.

Use:

```sh
python3 scripts/watch-ecosystem-prs.py
python3 scripts/watch-ecosystem-prs.py --comment
```

The first command reports active PRs that still need a redirect. The second posts
one idempotent coordination comment per active PR, using a hidden marker to avoid
duplicates.

## Optimal Defaults

- Keep meta checks fast and deterministic.
- Run heavyweight repo tests only after meta checks pass.
- Run E2E tests from built binaries or release artifacts, not copied source.
- Prefer contract fixtures for cross-repo assertions unless a live binary path is
  the behavior being tested.
- Record repo SHAs for every E2E run.
- Use separate temp data directories and ports per capability scenario.
- Cache build artifacts per repo, not in this root.

## Language Policy

These are Rust-first projects. Rust is the default for core systems paths,
daemons, security boundaries, storage engines, protocol/state machines, and
performance-sensitive code.

Rust is not mandatory everywhere. Use TypeScript for web/apps and SDK ergonomics,
Python for tests/tools/data workflows where it is materially faster to build and
maintain, Go/Java/etc. for client SDKs when ecosystem users expect them, and C/C++
or platform languages only when the platform boundary or measured hot path
justifies it.

Any non-Rust production component must name:

- Owner repo and package
- Boundary with Rust/core contracts
- Runtime/toolchain version
- Verification command in `ecosystem.toml`
- Interop contract or generated type source

## Gate Criteria

The ecosystem is uniform only when:

- `scripts/ecosystem-pipeline.sh report` produces no failures.
- `scripts/ecosystem-pipeline.sh gate` passes.
- Every repo-local migration queue has been removed or replaced by normal
  maintenance guidance.
- `ECOSYSTEM_RELEASE.toml` has real SHAs instead of `TODO`.
- Each capability in `ecosystem.toml` has a live or fixture-backed E2E scenario.
