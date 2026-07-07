#!/usr/bin/env python3
"""Ecosystem E2E scenario registry.

The scenarios are intentionally declared before every live path exists. This
keeps the missing E2E surface visible in the meta-repo without copying product
code here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]


def load() -> dict:
    return load_toml(ROOT / "ecosystem.toml")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    data = load()
    capabilities = data.get("capabilities", {})

    if args.list:
        for name, spec in capabilities.items():
            binaries = ", ".join(spec.get("binaries", []))
            contracts = ", ".join(spec.get("contracts", []))
            product = spec.get("product", spec["owner"])
            print(f"{name}: product={product} owner={spec['owner']} binaries=[{binaries}] contracts=[{contracts}]")
        return 0

    print("live ecosystem E2E execution is not wired yet")
    print("add scenario commands here as each capability fixture/live path lands")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
