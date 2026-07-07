#!/usr/bin/env python3
"""Check cross-repo manifest/tooling uniformity for the ecosystem meta-repo."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ecosystem.toml"
SKIP_DIRS = {".git", "node_modules", "target", "dist", "build", ".next", "__pycache__"}


def read_text(path: Path) -> str | None:
    try:
        return path.read_text()
    except FileNotFoundError:
        return None


def fail(errors: list[str], repo: str, message: str) -> None:
    errors.append(f"{repo}: {message}")


def parse_toml(path: Path) -> dict:
    return load_toml(path)


def package_json(path: Path) -> dict | None:
    text = read_text(path)
    if text is None:
        return None
    return json.loads(text)


def iter_files(root: Path, name: str):
    for path in root.rglob(name):
        if SKIP_DIRS.intersection(path.parts):
            continue
        yield path


def pyproject_project_fields(path: Path) -> dict:
    text = read_text(path) or ""
    project = re.search(r"(?ms)^\[project\]\s*(.*?)(?:^\[|\Z)", text)
    if not project:
        return {}
    body = project.group(1)
    fields: dict[str, str] = {}
    for key in ("requires-python", "license"):
        match = re.search(rf'(?m)^{re.escape(key)}\s*=\s*"([^"]+)"', body)
        if match:
            fields[key] = match.group(1)
            continue
        inline = re.search(rf'(?m)^{re.escape(key)}\s*=\s*\{{\s*text\s*=\s*"([^"]+)"\s*\}}', body)
        if inline:
            fields[key] = inline.group(1)
    return fields


def git_remote(path: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except subprocess.CalledProcessError:
        return None
    if out.startswith("git@github.com:"):
        out = "https://github.com/" + out.removeprefix("git@github.com:").removesuffix(".git")
    return out.removesuffix(".git")


def check_repo(name: str, spec: dict, policy: dict, errors: list[str]) -> None:
    path = ROOT / spec["path"]
    if not path.is_dir():
        fail(errors, name, f"missing repo path {path}")
        return

    if not (path / "AGENTS.md").exists() and not (path / "CLAUDE.md").exists():
        fail(errors, name, "missing AGENTS.md or CLAUDE.md for agent-visible migration tasks")

    actual_remote = git_remote(path)
    if actual_remote and actual_remote != spec["repository"]:
        fail(errors, name, f"origin remote {actual_remote!r} != manifest repository {spec['repository']!r}")

    cargo = path / "Cargo.toml"
    if spec.get("rust") and cargo.exists():
        cargo_text = read_text(cargo) or ""
        toolchain = parse_toml(path / "rust-toolchain.toml") if (path / "rust-toolchain.toml").exists() else None
        if toolchain is None:
            fail(errors, name, "missing rust-toolchain.toml")
        else:
            channel = toolchain.get("toolchain", {}).get("channel")
            if channel != policy["toolchain"]["rust_channel"]:
                fail(errors, name, f"rust-toolchain channel {channel!r} != {policy['toolchain']['rust_channel']!r}")
            components = set(toolchain.get("toolchain", {}).get("components", []))
            if not {"rustfmt", "clippy"}.issubset(components):
                fail(errors, name, "rust-toolchain must include rustfmt and clippy")

        for key, expected in (
            ("edition", policy["toolchain"]["rust_edition"]),
            ("rust-version", policy["toolchain"]["rust_version"]),
            ("license", spec["license"]),
            ("repository", spec["repository"]),
        ):
            pattern = rf'(?m)^{re.escape(key)}\s*=\s*"{re.escape(expected)}"\s*$'
            if not re.search(pattern, cargo_text):
                fail(errors, name, f"root Cargo.toml should set {key} = {expected!r}")

        rustfmt = read_text(path / "rustfmt.toml")
        if rustfmt is None:
            fail(errors, name, "missing rustfmt.toml")
        elif f'style_edition = "{policy["toolchain"]["rustfmt_style_edition"]}"' not in rustfmt:
            fail(errors, name, "rustfmt.toml should use style_edition = \"2024\"")

    if spec.get("node"):
        package_files = list(iter_files(path, "package.json"))
        if not package_files:
            fail(errors, name, "manifest marks node=true but no package.json was found")
        for pkg_path in package_files:
            pkg = package_json(pkg_path)
            if pkg is None:
                continue
            rel = pkg_path.relative_to(path)
            if not pkg.get("private") and pkg.get("license") and pkg["license"] != spec["license"]:
                fail(errors, name, f"{rel} license {pkg['license']!r} != {spec['license']!r}")
            if pkg_path.parent == path and "packageManager" not in pkg:
                fail(errors, name, f"{rel} should declare packageManager")

    if spec.get("python"):
        for pyproject in iter_files(path, "pyproject.toml"):
            project = pyproject_project_fields(pyproject)
            rel = pyproject.relative_to(path)
            if project:
                if project.get("requires-python") != policy["python"]["requires_python"]:
                    fail(errors, name, f"{rel} should set requires-python = {policy['python']['requires_python']!r}")
                license_value = project.get("license")
                if license_value and license_value != spec["license"]:
                    fail(errors, name, f"{rel} license {license_value!r} != {spec['license']!r}")


def main() -> int:
    data = parse_toml(MANIFEST)
    errors: list[str] = []
    for name, spec in data["repos"].items():
        check_repo(name, spec, data["policy"], errors)

    if errors:
        print("ecosystem uniformity check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("ecosystem uniformity check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
