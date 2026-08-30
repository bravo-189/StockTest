"""Manage the StockTest local web server and hourly refresh loop."""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_state(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}


def write_state(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def command_line(pid):
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return ""
    if pid <= 0:
        return ""
    if os.name == "nt":
        script = (
            f"$p = Get-CimInstance Win32_Process -Filter 'ProcessId = {pid}' -ErrorAction SilentlyContinue; "
            "if ($p) { $p.CommandLine }"
        )
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return completed.stdout.strip()
    try:
        return Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
    except OSError:
        return ""


def service_running(service):
    if not isinstance(service, dict):
        return False
    line = command_line(service.get("pid")).casefold()
    markers = [str(item).casefold() for item in service.get("markers", []) if item]
    return bool(line and markers and all(marker in line for marker in markers))


def public_service(service):
    return {
        "status": "running" if service_running(service) else "stopped",
        "pid": service.get("pid") if isinstance(service, dict) else None,
    }


def spawn(command, cwd, stdout_path, stderr_path):
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    popen_args = {
        "cwd": str(cwd),
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        popen_args["creationflags"] = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
    else:
        popen_args["start_new_session"] = True
    with stdout_path.open("a", encoding="utf-8") as stdout, stderr_path.open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, **popen_args)
    return process.pid


def runtime_status(state, project_root, port, interval_minutes):
    return {
        "projectRoot": str(project_root),
        "url": f"http://127.0.0.1:{port}/index.html",
        "port": port,
        "intervalMinutes": interval_minutes,
        "server": public_service(state.get("server")),
        "refresh": public_service(state.get("refresh")),
        "updatedAt": state.get("updatedAt"),
    }


def start_runtime(project_root, port, interval_minutes):
    project_root = project_root.resolve()
    runtime_dir = project_root / ".runtime"
    state_path = runtime_dir / "local_runtime.json"
    state = read_state(state_path)
    python = str(Path(sys.executable).resolve())

    if not service_running(state.get("server")):
        server_command = [python, "-u", "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(project_root)]
        state["server"] = {
            "pid": spawn(server_command, project_root, runtime_dir / "server.log", runtime_dir / "server-error.log"),
            "command": server_command,
            "markers": ["http.server", str(project_root)],
            "startedAt": timestamp(),
        }

    if not service_running(state.get("refresh")):
        refresh_script = project_root / "data_pipeline" / "refresh_local_data.py"
        refresh_command = [
            python,
            "-u",
            str(refresh_script),
            "--output-dir",
            str(project_root / "data"),
            "--interval-minutes",
            str(interval_minutes),
        ]
        state["refresh"] = {
            "pid": spawn(refresh_command, project_root, runtime_dir / "refresh.log", runtime_dir / "refresh-error.log"),
            "command": refresh_command,
            "markers": [str(refresh_script), str(project_root / "data")],
            "startedAt": timestamp(),
        }

    state.update({"port": port, "intervalMinutes": interval_minutes, "updatedAt": timestamp()})
    write_state(state_path, state)
    time.sleep(0.25)
    return state, runtime_status(state, project_root, port, interval_minutes)


def stop_service(service):
    if not service_running(service):
        return
    pid = int(service["pid"])
    if os.name == "nt":
        subprocess.run(
            ["taskkill.exe", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.time() + 5
    while time.time() < deadline and command_line(pid):
        time.sleep(0.1)


def stop_runtime(project_root, port, interval_minutes):
    project_root = project_root.resolve()
    state_path = project_root / ".runtime" / "local_runtime.json"
    state = read_state(state_path)
    stop_service(state.get("refresh"))
    stop_service(state.get("server"))
    state["updatedAt"] = timestamp()
    write_state(state_path, state)
    return runtime_status(state, project_root, port, interval_minutes)


def parse_args(argv=None):
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Manage StockTest local runtime")
    parser.add_argument("action", choices=("start", "status", "stop"))
    parser.add_argument("--project-root", type=Path, default=default_root)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--interval-minutes", type=float, default=60)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    project_root = args.project_root.resolve()
    state_path = project_root / ".runtime" / "local_runtime.json"
    if args.action == "start":
        _, result = start_runtime(project_root, args.port, args.interval_minutes)
    elif args.action == "stop":
        result = stop_runtime(project_root, args.port, args.interval_minutes)
    else:
        result = runtime_status(read_state(state_path), project_root, args.port, args.interval_minutes)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if args.action == "stop" or (result["server"]["status"] == "running" and result["refresh"]["status"] == "running") else 1


if __name__ == "__main__":
    raise SystemExit(main())
