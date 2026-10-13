#!/usr/bin/env python3
"""Execute declared capability scenarios and record owner commit receipts."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import tempfile
from pathlib import Path

from ecosystem_paths import repo_path
from ecosystem_toml import load as load_toml

ROOT = Path(__file__).resolve().parents[1]


def run_scenarios(data: dict, selected: set[str], *, timeout: float,
                  receipt: Path, root: Path = ROOT) -> int:
    capabilities = data.get("capabilities", {})
    unknown = selected - set(capabilities)
    if unknown:
        raise ValueError(f"Unknown capabilities: {', '.join(sorted(unknown))}")
    results = []
    for name, spec in capabilities.items():
        if name not in selected:
            continue
        item = {"capability": name, "owner": spec["owner"], "status": "blocked"}
        results.append(item)
        command = spec.get("e2e_command")
        owner = data.get("repos", {}).get(spec["owner"])
        if not command or not isinstance(command, list) or not all(isinstance(arg, str) for arg in command):
            item["reason"] = spec.get("registration_blocker", "No executable e2e_command declared; listing contracts is not verification")
            continue
        if owner is None:
            item["reason"] = "Owner repository is not declared"
            continue
        command = [arg.replace("{control_plane}", str(root)) for arg in command]
        checkout = repo_path(root, owner["path"])
        item.update(command=command, checkout=str(checkout))
        if not checkout.is_dir():
            item["reason"] = "Owner checkout is absent"
            continue
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout,
                             capture_output=True, text=True)
        if sha.returncode:
            item["reason"] = "Owner checkout has no readable commit SHA"
            continue
        item["head"] = sha.stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=checkout,
                               capture_output=True, text=True)
        if dirty.returncode:
            item["reason"] = "Cannot read owner worktree status before scenario"
            continue
        item["worktree_dirty"] = bool(dirty.stdout.strip())
        with tempfile.TemporaryFile() as log:
            try:
                process = subprocess.Popen(command, cwd=checkout, stdout=log,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
                item["returncode"] = process.returncode
                item["status"] = "passed" if process.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                item.update(status="failed", reason=f"Scenario exceeded {timeout:g}s")
            except OSError as exc:
                item.update(status="blocked", reason=str(exc))
            log.seek(0, 2)
            length = log.tell()
            log.seek(max(0, length - 16000))
            item["log_tail"] = log.read().decode("utf-8", errors="replace")
        after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout,
                               capture_output=True, text=True)
        if after.returncode or after.stdout.strip() != item["head"]:
            item.update(status="failed", reason="Owner HEAD changed during scenario")
        dirty_after = subprocess.run(["git", "status", "--porcelain"], cwd=checkout,
                                     capture_output=True, text=True)
        if dirty_after.returncode:
            item.update(status="failed", reason="Cannot read owner worktree status after scenario")
        else:
            item["worktree_dirty_after"] = bool(dirty_after.stdout.strip())
            if (item["worktree_dirty"] or item["worktree_dirty_after"]) and item["status"] == "passed":
                item.update(status="failed", reason="Owner worktree is dirty; output cannot attest its HEAD")
        print(f"{name}: {item['status']}", flush=True)
    complete = bool(results) and all(item["status"] == "passed" for item in results)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps({"complete": complete, "scope": sorted(selected),
                                   "results": results}, indent=2) + "\n")
    for item in results:
        if item["status"] != "passed":
            print(f"{item['capability']}: {item.get('reason', 'scenario failed')}")
    return 0 if complete else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="Inventory only; never a verification gate")
    parser.add_argument("--capability", action="append", help="Select capabilities; default all")
    parser.add_argument("--timeout", type=float, default=600)
    parser.add_argument("--receipt", type=Path, default=ROOT / "artifacts/e2e-receipt.json")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    data = load_toml(ROOT / "ecosystem.toml")
    capabilities = data.get("capabilities", {})
    if args.list:
        for name, spec in capabilities.items():
            print(f"{name}: owner={spec['owner']} command={spec.get('e2e_command', 'UNWIRED')}")
        return 0
    try:
        return run_scenarios(data, set(args.capability or capabilities),
                             timeout=args.timeout, receipt=args.receipt)
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
