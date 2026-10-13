"""The gate executes commands and never treats an inventory as evidence."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("e2e_runner", ROOT / "scripts/run-ecosystem-e2e.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "control"
        self.root.mkdir()
        self.owner = Path(self.temp.name) / "owner"
        self.owner.mkdir()
        subprocess.run(["git", "init", "-q", str(self.owner)], check=True)
        subprocess.run(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "--allow-empty", "-qm", "fixture"], cwd=self.owner, check=True)
        self.receipt = self.root / "receipt.json"

    def tearDown(self):
        self.temp.cleanup()

    def execute(self, command=None, timeout=5):
        scenario = {"owner": "owner"}
        if command is not None:
            scenario["e2e_command"] = command
        data = {"repos": {"owner": {"path": "owner"}}, "capabilities": {"fixture": scenario}}
        with patch.dict("os.environ", {"ECOSYSTEM_REPOS_ROOT": self.temp.name}):
            result = runner.run_scenarios(data, {"fixture"}, timeout=timeout,
                                          receipt=self.receipt, root=self.root)
        return result, json.loads(self.receipt.read_text())

    def test_executes_real_command_and_records_commit(self):
        result, receipt = self.execute([sys.executable, "-c", "print('executed')"])
        self.assertEqual(result, 0)
        self.assertTrue(receipt["complete"])
        self.assertIn("executed", receipt["results"][0]["log_tail"])
        self.assertEqual(len(receipt["results"][0]["head"]), 40)

    def test_control_plane_script_runs_from_owner_checkout(self):
        (self.root / "probe.py").write_text("from pathlib import Path; print(Path.cwd().name)")
        result, receipt = self.execute([sys.executable, "{control_plane}/probe.py"])
        self.assertEqual(result, 0)
        self.assertIn("owner", receipt["results"][0]["log_tail"])

    def test_unwired_scenario_fails(self):
        result, receipt = self.execute()
        self.assertEqual(result, 1)
        self.assertEqual(receipt["results"][0]["status"], "blocked")

    def test_failed_command_propagates(self):
        result, receipt = self.execute([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(result, 1)
        self.assertEqual(receipt["results"][0]["returncode"], 7)

    def test_timeout_is_failure(self):
        result, receipt = self.execute([sys.executable, "-c", "import time;time.sleep(20)"], .1)
        self.assertEqual(result, 1)
        self.assertIn("exceeded", receipt["results"][0]["reason"])

    def test_dirty_checkout_cannot_attest_head(self):
        (self.owner / "uncommitted.txt").write_text("changed")
        result, receipt = self.execute([sys.executable, "-c", "pass"])
        self.assertEqual(result, 1)
        self.assertIn("dirty", receipt["results"][0]["reason"])
