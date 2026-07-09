#!/usr/bin/env bash
set -euo pipefail

# Meta-repo smoke gate. This does not own product source code; it verifies that
# sibling repos still expose the declared tooling and binary surface.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT/scripts/check-ecosystem-binaries.py"
python3 "$ROOT/scripts/check-ecosystem-uniformity.py"
python3 "$ROOT/scripts/check-architecture-uniformity.py"
python3 "$ROOT/scripts/check-api-contracts.py" --service data-engine
python3 "$ROOT/scripts/run-ecosystem-e2e.py" --list
