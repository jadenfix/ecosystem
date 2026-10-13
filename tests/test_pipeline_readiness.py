"""Regression tests for checkout resolution and fail-closed E2E gates."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from ecosystem_paths import repo_path


class CheckoutTests(unittest.TestCase):
    def test_default_resolves_sibling_not_nested_checkout(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(repo_path(Path("/workspace/ecosystem"), "tempo"),
                             Path("/workspace/tempo"))

    def test_worktree_uses_explicit_product_root(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"ECOSYSTEM_REPOS_ROOT": directory}):
                self.assertEqual(repo_path(ROOT, "tempo"), Path(directory) / "tempo")

if __name__ == "__main__":
    unittest.main()
