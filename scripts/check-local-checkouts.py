#!/usr/bin/env python3
"""Audit local sibling checkout names and GitHub remotes.

This check is intentionally report-only. It does not rename directories or
rewrite remotes because these sibling repos may contain user work. It prints the
exact safe commands a human can run when ready.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "ecosystem.toml"


def normalize_remote(remote: str) -> str:
    remote = remote.strip()
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    if remote.endswith(".git"):
        remote = remote[:-4]
    return remote


def git_remote(path: Path) -> str | None:
    try:
        output = subprocess.check_output(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None
    return normalize_remote(output)


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit canonical ecosystem checkout names and remotes."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT.parent,
        help="directory containing sibling repo checkouts; defaults to this repo's parent",
    )
    args = parser.parse_args()

    data = load_toml(MANIFEST)
    checkout_root = args.root.resolve()
    aliases = data.get("checkout_aliases", {})
    problems: list[str] = []
    commands: list[str] = []

    for repo_key, spec in sorted(data["repos"].items()):
        canonical = checkout_root / spec["path"]
        expected_remote = normalize_remote(spec["repository"])
        alias_paths = [checkout_root / alias for alias in aliases.get(repo_key, [])]

        if canonical.is_dir():
            remote = git_remote(canonical)
            if remote and remote != expected_remote:
                problems.append(
                    f"{spec['product']}: {canonical.name} origin {remote!r} "
                    f"!= {expected_remote!r}"
                )
                commands.append(
                    f"git -C {shell_quote(str(canonical))} remote set-url origin "
                    f"{shell_quote(expected_remote + '.git')}"
                )
            continue

        existing_aliases = [path for path in alias_paths if path.is_dir()]
        if not existing_aliases:
            problems.append(
                f"{spec['product']}: missing canonical checkout {canonical}"
            )
            continue

        alias = existing_aliases[0]
        remote = git_remote(alias)
        problems.append(
            f"{spec['product']}: canonical checkout {canonical.name!r} is missing; "
            f"legacy alias {alias.name!r} exists"
        )
        commands.append(
            f"ln -s {shell_quote(alias.name)} {shell_quote(str(canonical))}"
        )
        if remote and remote != expected_remote:
            problems.append(
                f"{spec['product']}: alias {alias.name} origin {remote!r} "
                f"!= {expected_remote!r}"
            )
            commands.append(
                f"git -C {shell_quote(str(alias))} remote set-url origin "
                f"{shell_quote(expected_remote + '.git')}"
            )

    if problems:
        print("local checkout audit found mismatches:")
        for problem in problems:
            print(f"- {problem}")
        if commands:
            print("\nSuggested non-destructive alignment commands:")
            print(f"cd {shell_quote(str(checkout_root))}")
            for command in commands:
                print(command)
        return 1

    print(f"local checkout audit passed for {checkout_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
