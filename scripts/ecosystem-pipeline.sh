#!/usr/bin/env bash
set -u -o pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:-report}"

if [[ "$MODE" != "report" && "$MODE" != "gate" && "$MODE" != "meta" && "$MODE" != "repo" && "$MODE" != "e2e" ]]; then
  echo "usage: scripts/ecosystem-pipeline.sh [report|gate|meta|repo|e2e]" >&2
  exit 2
fi

failures=0

run_step() {
  local name="$1"
  shift
  echo "==> $name"
  if "$@"; then
    echo "ok: $name"
  else
    local code=$?
    echo "failed: $name (exit $code)" >&2
    failures=$((failures + 1))
    if [[ "$MODE" == "gate" || "$MODE" == "$name" ]]; then
      exit "$code"
    fi
  fi
}

run_meta() {
  run_step meta-binaries python3 "$ROOT/scripts/check-ecosystem-binaries.py"
  run_step meta-architecture python3 "$ROOT/scripts/check-architecture-uniformity.py"
  run_step meta-api-contracts python3 "$ROOT/scripts/check-api-contracts.py"
  run_step meta-uniformity python3 "$ROOT/scripts/check-ecosystem-uniformity.py"
}

run_repo() {
  run_step repo-verification python3 "$ROOT/scripts/run-ecosystem-verification.py" --continue-on-error
}

run_e2e() {
  run_step e2e-scenarios python3 "$ROOT/scripts/run-ecosystem-e2e.py" --list
}

case "$MODE" in
  meta)
    run_meta
    ;;
  repo)
    run_repo
    ;;
  e2e)
    run_e2e
    ;;
  report|gate)
    run_meta
    run_repo
    run_e2e
    ;;
esac

if [[ "$failures" -gt 0 ]]; then
  echo "ecosystem pipeline completed with $failures failing stage(s)" >&2
  exit 1
fi

echo "ecosystem pipeline passed"
