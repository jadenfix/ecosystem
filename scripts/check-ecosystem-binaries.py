#!/usr/bin/env python3
"""Check that each repo still declares the binaries named in ecosystem.toml."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]


def cargo_declared_bins(repo: Path) -> set[str]:
    bins: set[str] = set()
    for manifest in repo.rglob("Cargo.toml"):
        text = manifest.read_text()
        package_match = re.search(r'(?m)^name\s*=\s*"([^"]+)"', text)
        if package_match:
            # Cargo packages with src/main.rs can be bins without [[bin]]; keep
            # package names visible for the meta manifest.
            if (manifest.parent / "src" / "main.rs").exists():
                bins.add(package_match.group(1))
        for src_bin in (manifest.parent / "src" / "bin").glob("*.rs"):
            bins.add(src_bin.stem)
        for match in re.finditer(r'(?ms)^\[\[bin\]\].*?^name\s*=\s*"([^"]+)"', text):
            bins.add(match.group(1))
    return bins


def main() -> int:
    data = load_toml(ROOT / "ecosystem.toml")

    errors: list[str] = []
    for name, spec in data["repos"].items():
        repo = ROOT / spec["path"]
        declared = cargo_declared_bins(repo)
        for binary in spec.get("binaries", []):
            if binary not in declared:
                errors.append(f"{name}: binary {binary!r} not declared in Cargo manifests")

    if errors:
        print("ecosystem binary check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("ecosystem binary check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
