import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.request import urlopen


MANAGER = Path(__file__).with_name("local_runtime.py")


class LocalRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        (self.project_root / "data_pipeline").mkdir()
        (self.project_root / "index.html").write_text("runtime-ok", encoding="utf-8")
        (self.project_root / "data_pipeline" / "refresh_local_data.py").write_text(
            """import argparse, json, time
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--output-dir')
parser.add_argument('--interval-minutes')
args = parser.parse_args()
output = Path(args.output_dir)
output.mkdir(parents=True, exist_ok=True)
(output / 'refresh_status.json').write_text(json.dumps({'status': 'ok'}), encoding='utf-8')
while True:
    time.sleep(1)
""",
            encoding="utf-8",
        )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]

    def tearDown(self):
        if MANAGER.exists():
            self.run_manager("stop", check=False)
        self.temp_dir.cleanup()

    def run_manager(self, action, check=True):
        completed = subprocess.run(
            [
                sys.executable,
                str(MANAGER),
                action,
                "--project-root",
                str(self.project_root),
                "--port",
                str(self.port),
                "--interval-minutes",
                "60",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if check:
            self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        return json.loads(completed.stdout) if completed.stdout.strip() else {}

    def wait_until(self, predicate, timeout=8):
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if predicate():
                    return True
            except (OSError, ValueError):
                pass
            time.sleep(0.1)
        return False

    @unittest.skipUnless(os.name == "nt", "Windows process lifecycle")
    def test_runtime_lifecycle_starts_once_and_stops_owned_processes(self):
        first = self.run_manager("start")
        self.assertTrue(
            self.wait_until(lambda: urlopen(first["url"], timeout=1).read() == b"runtime-ok"),
            first,
        )
        self.assertTrue(
            self.wait_until(lambda: (self.project_root / "data" / "refresh_status.json").exists()),
            first,
        )
        running = self.run_manager("status")
        self.assertEqual(running["server"]["status"], "running")
        self.assertEqual(running["refresh"]["status"], "running")

        repeated = self.run_manager("start")
        self.assertEqual(repeated["server"]["pid"], running["server"]["pid"])
        self.assertEqual(repeated["refresh"]["pid"], running["refresh"]["pid"])

        stopped = self.run_manager("stop")
        self.assertEqual(stopped["server"]["status"], "stopped")
        self.assertEqual(stopped["refresh"]["status"], "stopped")

    @unittest.skipUnless(os.name == "nt", "Windows command wrapper")
    def test_status_wrapper_passes_exact_project_root(self):
        wrapper = Path(__file__).resolve().parents[1] / "status-local.cmd"
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", str(wrapper)],
            input="\n",
            capture_output=True,
            text=True,
            timeout=15,
        )
        start = completed.stdout.find("{")
        self.assertGreaterEqual(start, 0, completed.stderr or completed.stdout)
        payload, _ = json.JSONDecoder().raw_decode(completed.stdout[start:])
        self.assertEqual(Path(payload["projectRoot"]), wrapper.parent.resolve())


if __name__ == "__main__":
    unittest.main()
