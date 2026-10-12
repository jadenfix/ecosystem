"""Check that pipeline status reflects executed scenarios, not discovery."""

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def run_pipeline(self, mode, scenario_exit):
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / "scripts"
            scripts.mkdir()
            pipeline = scripts / "ecosystem-pipeline.sh"
            shutil.copyfile(ROOT / "scripts/ecosystem-pipeline.sh", pipeline)
            # Discovery can succeed even when scenario execution fails.
            (scripts / "run-ecosystem-e2e.py").write_text(
                "import sys\n"
                "if '--list' in sys.argv:\n"
                "    print('scenario discovered')\n"
                "    sys.exit(0)\n"
                "print('scenario executed')\n"
                f"sys.exit({scenario_exit})\n"
            )
            for checker in (
                "check-ecosystem-binaries.py",
                "check-architecture-uniformity.py",
                "check-ecosystem-uniformity.py",
                "run-ecosystem-verification.py",
            ):
                (scripts / checker).write_text("print('fixture check passed')\n")
            return subprocess.run(
                ["bash", str(pipeline), mode], capture_output=True, text=True
            )

    def test_failed_execution_cannot_pass_e2e_stage(self):
        result = self.run_pipeline("e2e", 7)
        self.assertEqual(result.returncode, 1)
        self.assertIn("scenario executed", result.stdout)
        self.assertIn("failed: e2e-scenarios (exit 7)", result.stderr)
        self.assertNotIn("ecosystem pipeline passed", result.stdout)

    def test_gate_propagates_scenario_exit_code(self):
        result = self.run_pipeline("gate", 7)
        self.assertEqual(result.returncode, 7)
        self.assertIn("scenario executed", result.stdout)

    def test_success_requires_execution(self):
        result = self.run_pipeline("e2e", 0)
        self.assertEqual(result.returncode, 0)
        self.assertIn("scenario executed", result.stdout)
        self.assertIn("ecosystem pipeline passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
