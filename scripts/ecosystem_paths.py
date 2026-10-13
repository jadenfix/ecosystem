"""Locate product checkouts separately from the ecosystem control plane."""

from __future__ import annotations

import os
from pathlib import Path


def repo_path(control_plane: Path, relative_path: str) -> Path:
    """Use sibling checkouts, or an explicit root for worktrees/CI checkouts.

    ECOSYSTEM_REPOS_ROOT identifies the directory containing the products. It
    never changes where ecosystem.toml or the control-plane scripts are read.
    """
    configured = os.environ.get("ECOSYSTEM_REPOS_ROOT")
    checkout_root = Path(configured).expanduser().resolve() if configured else control_plane.parent
    return checkout_root / relative_path
