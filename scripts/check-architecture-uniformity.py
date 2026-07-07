#!/usr/bin/env python3
"""Lightweight architecture-shape check for ecosystem repos."""

from __future__ import annotations

import re
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_DOC_TERMS = (
    "Repo",
    "Commands",
    "contract",
    "storage",
)


def read(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return ""


def has_workspace_package(cargo: str) -> bool:
    return "[workspace.package]" in cargo


def has_workspace_deps(cargo: str) -> bool:
    return "[workspace.dependencies]" in cargo


def has_thin_binary_shape(repo: Path, binaries: list[str]) -> bool:
    # This is intentionally structural: declared binaries are checked elsewhere.
    # Here we require at least one binary crate or src/main.rs when binaries are
    # part of the repo contract.
    if not binaries:
        return True
    for manifest in repo.rglob("Cargo.toml"):
        text = read(manifest)
        if "[[bin]]" in text or (manifest.parent / "src" / "main.rs").exists():
            return True
    return False


def main() -> int:
    data = load_toml(ROOT / "ecosystem.toml")

    errors: list[str] = []
    for name, spec in data["repos"].items():
        repo = ROOT / spec["path"]
        agent_doc = read(repo / "AGENTS.md") + "\n" + read(repo / "CLAUDE.md")
        cargo = read(repo / "Cargo.toml")

        if spec.get("rust"):
            if not has_workspace_package(cargo):
                errors.append(f"{name}: root Cargo.toml should use [workspace.package]")
            if not has_workspace_deps(cargo):
                errors.append(f"{name}: root Cargo.toml should use [workspace.dependencies]")
            if not has_thin_binary_shape(repo, spec.get("binaries", [])):
                errors.append(f"{name}: expected binary shape was not found")

        missing_terms = [term for term in REQUIRED_DOC_TERMS if term.lower() not in agent_doc.lower()]
        if missing_terms:
            errors.append(f"{name}: agent docs missing architecture terms: {', '.join(missing_terms)}")

        if re.search(r"backward compat|compatibility shim|legacy alias", agent_doc, re.I):
            if "Backward compatibility is not required" not in agent_doc:
                errors.append(f"{name}: legacy compatibility language must be scoped to pre-adoption breakage policy")

    if errors:
        print("architecture uniformity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("architecture uniformity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
