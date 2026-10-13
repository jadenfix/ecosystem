#!/usr/bin/env python3
"""Run Tempo's exact live-CDP CI stages; reject absent/skipped browser tests."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

STAGES = [
    (["cargo", "test", "--locked", "-p", "tempo-engine-cdp", "live_cdp", "--", "--nocapture", "--test-threads=1"],
     ["live_cdp_driver_passes_conformance_v2 ... ok", "live_cdp_driver_navigates_observes_acts_and_screenshots ... ok"]),
    (["cargo", "test", "--locked", "-p", "tempo-engine-cdp", "--test", "uds_driver", "--", "--nocapture", "--test-threads=1"],
     ["cdp_driver_serves_commands_over_engine_host_uds ... ok"]),
    (["cargo", "test", "--locked", "-p", "tempo-agent", "live_cdp", "--", "--nocapture", "--test-threads=1"],
     ["live_cdp_runner_completes_scripted_task_and_journals_it ... ok"]),
    (["cargo", "test", "--locked", "-p", "tempo-cli", "--test", "run_decided_task", "--", "--nocapture", "--test-threads=1"],
     ["run_decided_task_binary_drives_live_cdp_with_scripted_decider ... ok"]),
]


def main() -> int:
    browser = os.environ.get("TEMPO_CDP_CHROME")
    if not browser or not Path(browser).is_file():
        raise RuntimeError("TEMPO_CDP_CHROME must identify the installed real Chrome binary")
    subprocess.run([browser, "--version"], check=True, timeout=15)
    for command, markers in STAGES:
        result = subprocess.run(command, capture_output=True, text=True, timeout=600)
        output = result.stdout + result.stderr
        print(output[-16000:], flush=True)
        if result.returncode:
            return result.returncode
        if "skipping live CDP" in output or any(marker not in output for marker in markers):
            raise RuntimeError("Live CDP stage was skipped or required native assertion did not run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
