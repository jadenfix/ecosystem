# Tempera Architecture Uniformity Policy

The Tempera ecosystem should feel like one system even though the product code
remains in separate repos. Until public users depend on compatibility, prefer
breaking cleanup over adapters, aliases, duplicate package shapes, or legacy
defaults.

## Shared Repo Shape

Every repo should converge on this architecture:

- Root manifest owns workspace/package metadata.
- Thin binaries live at explicit binary crates/packages and call library APIs.
- Library crates own domain behavior, contracts, storage adapters, and tests.
- Generated artifacts are regenerated from source contracts, not edited by hand.
- Docs name the shipped behavior separately from roadmap behavior.
- Local developer commands and CI commands are the same commands listed in
  `ecosystem.toml`.

## Shared Runtime Shape

Every daemon/runtime should expose:

- `--version` with repo name, package version, git SHA, Rust/Node/Python version
  where applicable, and build profile.
- Health/readiness command or endpoint.
- Structured logs.
- Metrics or explicit reason why not applicable.
- Trace/span propagation where it participates in E2E flows.
- Config loading with documented precedence.
- Fail-closed auth/policy defaults.

## Shared Contract Shape

Each public package or binary must identify its source contract:

- Palette: OpenAPI/OTLP/MCP/SDK contract. Current repo: `jadenfix/palette`.
- tempo: compiled observation, policy, tool execution, session/cassette
  contract.
- cradle: sandbox job and network/secrets policy contract. Current repo:
  `jadenfix/cradle`.
- temp.js: runtime bridge and generated access-surface contract. Current repo:
  `jadenfix/temp.js`.
- tempOS: capability grant, policy decision, receipt, and audit journal
  contract.
- remi: memory record and retrieval contract. Current repo: `jadenfix/remi`.
- Arrha: transaction, receipt, settlement, and indexer contract. Current repo:
  `jadenfix/arrha`.

## Storage Shape

Use the same workload split everywhere:

- Embedded local state: SQLite latest stable, or a repo-specific local journal
  when append-only audit is the contract.
- Relational/control-plane state: PostgreSQL latest supported stable.
- Trace/event analytics: ClickHouse LTS for production analytics.
- Ledger/node state: RocksDB for Arrha unless replacement benchmarks prove a
  better option.
- Durable audit/receipt logs: append-only, checksummed, replayable, and
  migration-aware.

## Breaking Change Rule

Because these packages are not yet public dependency surfaces, agents should
prefer strong uniform migrations:

- Remove stale aliases instead of preserving them.
- Regenerate clients and fixtures in the same PR as the contract change.
- Update every caller in the same repo instead of adding compatibility shims.
- Document the break in `ECOSYSTEM_RELEASE.toml` or the PR body.
- Keep append-only database migrations; breaking API compatibility does not
  permit rewriting applied data migrations.
