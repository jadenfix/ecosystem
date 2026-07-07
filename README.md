# Tempera Ecosystem Meta-Repo

This directory is the control plane for the Tempera sibling repos in this
workspace. It does not vendor product source code. It points to each repo,
declares the expected binaries and package surfaces, and runs cross-repo checks
so the ecosystem stays uniform.

## Product Names

The top coordination repo is `jadenfix/ecosystem`. These are the canonical
product names, GitHub repositories, and expected sibling checkout names:

- `Palette`: observability/evals/API product, current repo `jadenfix/palette`
- `temp.js`: language/runtime bridge, current repo `jadenfix/temp.js`
- `tempo`: browser/headless product, current repo `jadenfix/tempo`
- `tempOS`: OS/runtime admission product, current repo `jadenfix/tempOS`
- `remi`: memory product, current repo `jadenfix/remi`
- `cradle`: sandbox execution product, current repo `jadenfix/cradle`
- `Arrha`: settlement/chain/credits product, current repo `jadenfix/arrha`

Legacy Beater-family names are no longer public product names. Keep them only
where a repo-local binary, crate, package, or fixture still has to be migrated in
its own PR.

## What This Owns

- `ecosystem.toml`: repo registry, target toolchains, storage policy, expected
  binaries, and verification commands.
- `AGENTS.md`: migration rules for coding agents.
- `scripts/check-ecosystem-binaries.py`: verifies declared binaries still exist.
- `scripts/check-ecosystem-uniformity.py`: verifies manifests match the target
  state after migrations land.
- `scripts/run-ecosystem-verification.py`: runs declared per-repo verification
  commands.
- `scripts/ecosystem-pipeline.sh`: staged report/gate pipeline for meta, repo,
  and E2E checks.
- `scripts/watch-ecosystem-prs.py`: watches active PRs across sibling repos and
  posts one ecosystem compatibility redirect when needed.
- `docs/api-sdk-mcp-shape.md`: shared API, SDK, CLI, auth, error, and MCP shape
  profile for public client-facing surfaces.
- `scripts/audit-openapi-shape.py`: portable OpenAPI profile audit for REST
  services.
- `docs/ecosystem-pipeline.md`: pipeline and language policy.
- `scripts/ecosystem-smoke.sh`: root smoke gate for meta-repo checks.

## Target Outcome

After the migration queues are complete, every repo should agree on:

- Latest stable Rust pinned in `rust-toolchain.toml`
- Rust 2024 edition and matching MSRV
- Repo-local formatting and lint policy
- Actual GitHub repository metadata
- License metadata matching each repo's `LICENSE`
- npm/Node/Python package baselines where applicable
- Workload-appropriate storage choices and append-only migration discipline
- Declared binaries that can be built, launched, and tested from this root
- Similar architecture in every repo: thin binaries, library-owned behavior,
  generated contracts, version/health/smoke surfaces, and documented storage
  boundaries
- One public client-facing shape for services: canonical operation names, shared
  error envelopes, consistent SDK config, CLI flags/env vars, auth handling, and
  MCP/tool projections that derive from or drift-check against the same contract
- Rust-first implementation by default, while allowing TypeScript, Python,
  platform languages, and SDK languages when they are the better fit and their
  boundary is explicit and tested

## Commands

```sh
scripts/ecosystem-pipeline.sh report
scripts/ecosystem-pipeline.sh gate
python3 scripts/check-ecosystem-binaries.py
python3 scripts/check-ecosystem-uniformity.py
python3 scripts/run-ecosystem-verification.py --list
python3 scripts/run-ecosystem-verification.py --repo tempo
python3 scripts/watch-ecosystem-prs.py
scripts/ecosystem-smoke.sh
```

`check-ecosystem-uniformity.py` is expected to fail until the repo-local
migration tasks are completed. That failure is useful: it is the remaining work
list made executable.
