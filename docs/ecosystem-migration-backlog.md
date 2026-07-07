# Tempera Ecosystem Migration Backlog

Delete tasks only after the corresponding repo is migrated, formatted, tested,
and the meta-repo checks agree.

## Phase 1: Meta-Repo Control Plane

- [ ] Keep `ecosystem.toml` as the single registry of repos, binaries, storage
  roles, and verification commands.
- [ ] Keep the Tempera product naming map current: Palette (`jadenfix/palette`),
  temp.js (`jadenfix/temp.js`), tempo (`jadenfix/tempo`), tempOS
  (`jadenfix/tempOS`), remi (`jadenfix/remi`), cradle (`jadenfix/cradle`), and
  Arrha (`jadenfix/arrha`). The top coordination repo is `jadenfix/ecosystem`.
- [ ] Keep this root free of product source code. Use sibling repo paths,
  worktrees, submodules, or release artifacts; do not copy crates/apps here.
- [ ] Make `scripts/check-ecosystem-binaries.py` pass.
- [ ] Make `scripts/run-ecosystem-verification.py --list` show every repo and
  expected command.
- [ ] Use `scripts/ecosystem-pipeline.sh report` during migration and
  `scripts/ecosystem-pipeline.sh gate` once drift is removed.

## Phase 2: Uniform Toolchains

- [ ] Verify latest stable Rust at migration time and update
  `ecosystem.toml [policy.toolchain]`.
- [ ] Add or update every repo `rust-toolchain.toml`.
- [ ] Normalize Rust edition/MSRV/rustfmt/lints per the root `AGENTS.md`.
- [ ] Make `scripts/check-ecosystem-uniformity.py` pass for Rust metadata.

## Phase 3: Package Metadata

- [ ] Normalize npm package manager and Node engine policy.
- [ ] Normalize Python package metadata to PEP 621 where hand-authored.
- [ ] Fix stale repository URLs and placeholder generated-client metadata.
- [ ] Ensure license metadata matches each repo's actual `LICENSE`.
- [ ] Make all first-party package versions lockstep at the root ecosystem
  version while pre-1.0. Remove incompatible old package names or aliases instead
  of preserving them.

## Phase 3.5: Architecture Uniformity

- [ ] Make every binary thin over library crates, with one obvious command path
  for health/version/smoke behavior.
- [ ] Make every public contract source-owned: no hand-edited generated clients,
  schemas, OpenAPI snapshots, or fixture outputs.
- [ ] Make every daemon/runtime expose version metadata, structured logs,
  health/readiness, and a documented config precedence model.
- [ ] Ensure each repo has equivalent docs sections for repo shape, commands,
  contracts, storage, security boundaries, and migration tasks.
- [ ] Remove old compatibility shims unless an explicit pre-1.0 launch scenario
  still needs them.
- [ ] Apply the Rust-first, best-language-wins policy from
  `docs/ecosystem-pipeline.md`. Non-Rust production components must have an
  owner, boundary, runtime version, verification command, and interop contract.

## Phase 4: Storage And Migration Policy

- [ ] Palette: keep SQLite for local OSS runtime, PostgreSQL for relational
  scale/control-plane paths, ClickHouse LTS for trace analytics, and append-only
  SQL migrations with checksums.
- [ ] Arrha: keep RocksDB for node state unless benchmark evidence proves a
  better engine; use PostgreSQL only for indexer/control-plane projections where
  appropriate.
- [ ] tempo/tempOS: keep append-only journals/cassettes/receipts as durability
  contracts and document when SQLite is used for local indexed state.
- [ ] cradle/temp.js/remi: use embedded local state only when the
  workload is single-node/local; add migration checks before adding server DBs.

## Phase 5: E2E Capabilities

- [ ] Palette can ingest a trace, query it, and serve dashboard/API contract
  surfaces.
- [ ] tempo can produce a compiled observation and run tool execution policy.
- [ ] cradle can execute a sandboxed job with denied network/secrets by default.
- [ ] temp.js can run the agent runtime bridge against declared binaries or
  contract fixtures.
- [ ] tempOS can admit a tool action, execute it through policy, and emit a
  receipt/audit trail.
- [ ] remi can write/read/retrieve memory records through the declared
  binary or SDK.
- [ ] Arrha can run a local node/devnet smoke and expose SDK/indexer surfaces.
- [ ] The root meta-repo can run a composed smoke that records repo SHAs,
  binaries, ports, storage modes, and pass/fail status.
