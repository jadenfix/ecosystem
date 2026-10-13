# Executable capability gates

`--list` reports the inventory and never verifies an integration. The pipeline E2E stage now executes declared `e2e_command` arrays from each owning sibling checkout. Missing commands, missing checkouts, nonzero exits, timeouts, dirty worktrees, and a changed HEAD fail the gate.

```sh
ECOSYSTEM_REPOS_ROOT=/path/to/products python3 scripts/run-ecosystem-e2e.py
ECOSYSTEM_REPOS_ROOT=/path/to/products python3 scripts/run-ecosystem-e2e.py --capability memory --timeout 600
python3 -m unittest discover -s tests -v
```

Each selected scenario writes its command, owner HEAD, dirty status, exit status, and bounded log tail to `artifacts/e2e-receipt.json`. A selected subset receipt is scoped to that subset and does not claim ecosystem completion. Keep source checkouts clean and use `CARGO_TARGET_DIR` outside them when needed.

The memory scenario invokes the real `remi/scripts/e2e-memory.sh` CLI/HTTP/SQLite workflow. Five additional owner workflows are registered: Palette product-loop trace/MCP/SDK/compose gate (Docker required, skips disabled); Tempo exact live-CDP CI stages (real browser required, missing/skipped test assertions rejected); Cradle native Wasm CLI/API/MCP/SQLite; temp.js authenticated remote MCP bridge and journal; tempOS token-gated admission/execution/receipt verification. Each requires its real native runtime/build dependencies. Settlement remains blocked until a transaction → receipt → indexer workflow exists; validator or mocked SDK tests do not substitute for that intent. Controller tests exercise real subprocesses in a tiny committed fixture repo; they verify gating behavior and are not product E2E evidence.
