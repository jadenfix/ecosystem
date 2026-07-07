#!/usr/bin/env python3
"""Run per-repo verification commands declared in ecosystem.toml."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]


def load() -> dict:
    return load_toml(ROOT / "ecosystem.toml")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", help="Repo key to verify; repeatable")
    parser.add_argument("--list", action="store_true", help="List configured commands")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    data = load()
    selected = set(args.repo or data["repos"].keys())
    unknown = selected - set(data["repos"].keys())
    if unknown:
        print(f"unknown repo(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    if args.list:
        for name, spec in data["repos"].items():
            if name not in selected:
                continue
            product = spec.get("product", name)
            print(f"{product} / {name} ({spec['path']})")
            for command in spec.get("verify", []):
                print(f"  {command}")
        return 0

    failures: list[str] = []
    for name, spec in data["repos"].items():
        if name not in selected:
            continue
        repo = ROOT / spec["path"]
        for command in spec.get("verify", []):
            print(f"==> {name}: {command}", flush=True)
            result = subprocess.run(command, cwd=repo, shell=True)
            if result.returncode:
                failures.append(f"{name}: {command} exited {result.returncode}")
                if not args.continue_on_error:
                    break
        if failures and not args.continue_on_error:
            break

    if failures:
        print("ecosystem verification failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ecosystem verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
