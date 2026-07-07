#!/usr/bin/env python3
"""Watch open ecosystem PRs and optionally redirect active agents.

This script uses `gh` because PR monitoring/commenting is operational GitHub
work, not product code. It is intentionally root-owned so every repo gets the
same monitoring policy.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ecosystem_toml import load as load_toml


ROOT = Path(__file__).resolve().parents[1]
MARKER = "TEMPERA_COMPATIBILITY_REDIRECT_v4"
LEGACY_MARKER = "ecosystem root now has a compatibility/uniformity control plane"


COMMENT = f"""<!-- {MARKER} -->
Coordination note for the next agent turns: the Tempera ecosystem root now has a compatibility/uniformity control plane (`ecosystem.toml`, `AGENTS.md`, `docs/ecosystem-pipeline.md`, `docs/architecture-uniformity.md`, and `scripts/ecosystem-pipeline.sh`).

Please make the next sequence of work compatible with that pipeline before expanding feature scope. Focus on the repo-local migration queue: latest stable Rust target, Rust 2024/MSRV alignment, Tempera product naming, package/license/repository metadata, storage policy, thin-binary architecture, generated-contract discipline, package sync, and E2E capability hooks.

Canonical Tempera product names:
- Top coordination repo: `jadenfix/ecosystem`
- Palette: current repo `jadenfix/palette`
- temp.js: current repo `jadenfix/temp.js`
- tempo: current repo `jadenfix/tempo`
- tempOS: current repo `jadenfix/tempOS`
- remi: current repo `jadenfix/remi`
- cradle: current repo `jadenfix/cradle`
- Arrha: current repo `jadenfix/arrha`

Backward compatibility is not required pre-adoption; prefer the clean uniform breaking migration over shims/aliases. From the ecosystem root, use `scripts/ecosystem-pipeline.sh report` as the drift list and only delete migration tasks once the relevant checks pass.
"""


def run_json(args: list[str]):
    out = subprocess.check_output(args, text=True)
    return json.loads(out)


def run(args: list[str]) -> None:
    subprocess.check_call(args)


def repo_full_name(spec: dict) -> str:
    url = spec["repository"].removesuffix(".git")
    return url.removeprefix("https://github.com/")


def is_agent_pr(pr: dict) -> bool:
    head = pr.get("headRefName", "").lower()
    title = pr.get("title", "").lower()
    return any(token in head or token in title for token in ("codex", "claude", "agent"))


def has_redirect(repo: str, number: int) -> bool:
    comments = run_json([
        "gh",
        "pr",
        "view",
        str(number),
        "--repo",
        repo,
        "--json",
        "comments",
    ]).get("comments", [])
    for comment in comments:
        body = comment.get("body", "")
        if MARKER in body or LEGACY_MARKER in body:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--active-hours", type=int, default=96)
    parser.add_argument("--comment", action="store_true", help="Post redirect comments to active PRs missing one")
    parser.add_argument("--agent-only", action="store_true", help="Only include PRs with codex/claude/agent in branch or title")
    args = parser.parse_args()

    data = load_toml(ROOT / "ecosystem.toml")
    cutoff = datetime.now(timezone.utc) - timedelta(hours=args.active_hours)
    rows: list[tuple[str, int, str, str, bool, bool, bool]] = []
    seen_repos: set[str] = set()

    for name, spec in data["repos"].items():
        repo = repo_full_name(spec)
        if repo in seen_repos:
            continue
        seen_repos.add(repo)
        prs = run_json([
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "50",
            "--json",
            "number,title,updatedAt,isDraft,headRefName,url",
        ])
        for pr in prs:
            updated = datetime.fromisoformat(pr["updatedAt"].replace("Z", "+00:00"))
            active = updated >= cutoff
            agent = is_agent_pr(pr)
            if not active:
                continue
            if args.agent_only and not agent:
                continue
            redirected = has_redirect(repo, pr["number"])
            if args.comment and not redirected:
                run(["gh", "pr", "comment", str(pr["number"]), "--repo", repo, "--body", COMMENT])
                redirected = True
            rows.append((repo, pr["number"], pr["title"], pr["url"], pr["isDraft"], redirected, agent))

    if not rows:
        print("No active ecosystem PRs matched the watch policy.")
        return 0

    print("Active ecosystem PR watch:")
    for repo, number, title, url, draft, redirected, agent in rows:
        status = "redirected" if redirected else "needs-redirect"
        draft_text = "draft" if draft else "ready"
        agent_text = "agent-like" if agent else "active"
        print(f"- {repo}#{number} [{draft_text}] [{agent_text}] [{status}] {title} ({url})")

    missing = [row for row in rows if not row[5]]
    if missing and not args.comment:
        print(f"\n{len(missing)} active PR(s) need redirect comments. Re-run with --comment to post them.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
