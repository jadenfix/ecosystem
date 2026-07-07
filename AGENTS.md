# Tempera Ecosystem Agent Migration Queue

This workspace contains separate repos, not one monorepo. Treat this file as the
cross-repo migration charter for Tempera coding agents; repo-local `AGENTS.md`
or `CLAUDE.md` files contain the actionable queue for each checkout.

## Product Name Map

Use these names in new docs, PRs, issues, and user-facing planning. The top
coordination repo is `jadenfix/ecosystem`. Use the canonical GitHub product
repos below, and expect sibling checkout folders to use the same product names.

- `Palette`: current repo `jadenfix/palette`
- `temp.js`: current repo `jadenfix/temp.js`
- `tempo`: current repo `jadenfix/tempo`
- `tempOS`: current repo `jadenfix/tempOS`
- `remi`: current repo `jadenfix/remi`
- `cradle`: current repo `jadenfix/cradle`
- `Arrha`: current repo `jadenfix/arrha`

## Uniform Target

Use these defaults unless a repo-local task says otherwise:

- Rust toolchain: before migration, verify the latest stable Rust from the
  official Rust release page and update `ecosystem.toml` if it moved. Checked on
  2026-07-06: latest stable is `1.96.1`; use `rust-version = "1.96"` and edition
  `2024` for active first-party crates.
- Cargo metadata: root `[workspace.package]` owns version, edition,
  rust-version, license, repository, and member crates inherit it.
- Cargo lints: forbid unsafe by default and deny `unwrap_used` / `expect_used`
  through workspace lints; add member `lints.workspace = true` where needed.
- Rust formatting: keep one repo-level `rustfmt.toml` with
  `style_edition = "2024"` unless generated code requires isolation.
- Node: use npm because these repos already carry npm lockfiles. Pin
  `packageManager`, run app/tool packages on the latest Active LTS line
  (`node >=24 <27` as of 2026-07-06), and keep published SDK compatibility
  broader only when CI tests that promise.
- TypeScript: authored packages should be ESM (`"type": "module"`); generated
  clients and tool runners may stay CommonJS when their generator/runtime needs
  it.
- Python: prefer PEP 621 `pyproject.toml`; migrate Poetry-generated clients only
  when the generator supports it cleanly.
- Language: these are Rust-first projects, especially for core systems paths,
  daemons, storage, security boundaries, protocol/state machines, and hot paths.
  Do not exclude other languages. Use TypeScript, Python, Go, Java, Swift,
  Kotlin, C/C++, or another language when it is the better tool for the
  subsystem; the boundary must be explicit, typed/generated where practical, and
  covered by the ecosystem pipeline.
- Storage: do not pretend one database is best for every workload. Use
  PostgreSQL latest supported stable for relational/control-plane state, SQLite
  latest stable for local embedded daemon/app state, ClickHouse latest LTS for
  trace/event analytics, RocksDB for Arrha node state unless benchmarks prove a
  better engine, and append-only checksummed journals for audit/receipt logs.
- Licenses: do not normalize licenses across repos by preference. Manifest
  license fields must match the repo's `LICENSE` file and published package
  intent.
- Repository URLs: use the actual GitHub remotes under `jadenfix`, not stale
  placeholder orgs.

## Execution Rules

- Do one repo per PR unless the change is pure documentation.
- Prefer complete migrations over partial churn: manifest updates, lockfiles,
  formatting, lint inheritance, docs, and verification should land together.
- If an agent is already active on a PR, its next sequence of turns should first
  reconcile that repo/PR with the ecosystem pipeline before adding unrelated
  product scope. Treat `scripts/ecosystem-pipeline.sh report` as the handoff
  checklist.
- Subagents should start at the top `jadenfix/ecosystem` control plane, read
  this file plus `docs/ecosystem-pipeline.md`, then move into one repo using the
  repo-local `AGENTS.md` queue. Do not let subagents invent per-repo standards.
- Backward compatibility is not required yet. Prefer breaking changes that make
  the architecture uniform, remove stale names, or align contracts. Update every
  caller/client/fixture in the same slice instead of carrying compatibility
  shims.
- "Too much engineering" is not a blocker when the extra work creates a durable
  invariant, test matrix, migration script, or CI gate. It is a blocker when it
  only adds abstraction without proving uniformity or performance.
- Optimize for current stable production tooling, reproducibility, and fast local
  verification. Record any reason to stay behind the uniform target in the
  repo-local agent file.
- Delete a repo-local migration task only after the repo is migrated, formatted,
  tested, and the reason is visible in the PR.
- This root is the ecosystem meta-repo. It does not vendor product code. It owns
  `ecosystem.toml`, `scripts/check-ecosystem-*.py`, and E2E verification wiring
  that points at sibling repos and their binaries.

## Next Meta-Repo Tasks

Delete each item only after it is complete and verified.

- [ ] Make `scripts/ecosystem-smoke.sh` pass after all repo-local migration
  queues are complete.
- [ ] Add CI for this meta-repo that runs binary, uniformity, and selected E2E
  checks against sibling checkouts or checked-out submodules/worktrees.
- [ ] Add a release-sync report that prints each repo SHA, toolchain, package
  manager, primary binaries, storage engines, and verification status.
- [ ] Run `python3 scripts/watch-ecosystem-prs.py` during coordination passes.
  Use `--comment` when active agent PRs have not been redirected to ecosystem
  compatibility work.
- [ ] Add E2E scenario fixtures for the core capabilities: Palette trace ingest,
  tempo browser/headless observation, cradle sandbox execution, temp.js agent
  runtime bridge, tempOS tool admission/receipt, remi retrieval, and Arrha
  settlement/indexer flow.
- [ ] Finish repo-local rename migrations so package names, binary names,
  generated clients, docs, fixtures, and local checkout folders converge on the
  Tempera product names above. Do not rename GitHub repositories through
  automation unless the user explicitly asks for remote repo renames.
- [ ] Enforce `docs/architecture-uniformity.md` across every repo. Remove
  repo-local exceptions unless they have benchmark, security, or product evidence.
- [ ] Promote `scripts/ecosystem-pipeline.sh gate` to the required CI path once
  `report` mode has no failures.
