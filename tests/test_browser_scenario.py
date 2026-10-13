"""Controller regression: absent or skipped Chrome is never browser proof."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/scenarios/browser-observation.py"
spec = importlib.util.spec_from_file_location("browser_scenario", SCRIPT)
scenario = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scenario)


class BrowserScenarioTests(unittest.TestCase):
    def test_missing_browser_is_rejected_before_cargo(self):
        with patch.dict("os.environ", {"TEMPO_CDP_CHROME": ""}), patch.object(scenario.subprocess, "run") as run:
            with self.assertRaisesRegex(RuntimeError, "real Chrome"):
                scenario.main()
            run.assert_not_called()

    def test_zero_or_skipped_native_tests_cannot_pass(self):
        with tempfile.NamedTemporaryFile() as browser:
            responses = [subprocess.CompletedProcess([], 0),
                         subprocess.CompletedProcess([], 0, "test result:ok.0 passed; skipping live CDP", "")]
            with patch.dict("os.environ", {"TEMPO_CDP_CHROME": browser.name}), patch.object(scenario.subprocess, "run", side_effect=responses):
                with self.assertRaisesRegex(RuntimeError, "skipped"):
                    scenario.main()
