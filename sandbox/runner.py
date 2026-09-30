"""Executes untrusted, LLM-generated code safely.

Two isolation levels are supported:

1. Docker (preferred) — runs inside a disposable container with:
   - no network access (--network none)
   - a memory cap (--memory) and CPU cap (--cpus)
   - a read-only bind mount of the generated file
   - a hard wall-clock timeout enforced from the host

2. subprocess fallback — used automatically if Docker is not installed
   or not running. This is what the original reference project
   (souvikghosh/coding-agent) uses: an isolated subprocess with a
   timeout. It is real isolation from the parent process, but it does
   NOT sandbox filesystem, network, or resource usage the way Docker
   does — generated code can still read/write the filesystem or make
   network calls in this mode. Prefer Docker whenever it's available.
"""

import os
import shutil
import subprocess
import sys
import tempfile

SANDBOX_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_TAG = "coding-agent-sandbox"

DOCKER_TIMEOUT_SECONDS = 15
SUBPROCESS_TIMEOUT_SECONDS = 10


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
            check=True,
        )
        return True
    except Exception:
        return False


def _ensure_sandbox_image() -> bool:
    """Builds the sandbox image if it doesn't exist yet. Returns True if ready."""
    check = subprocess.run(
        ["docker", "image", "inspect", IMAGE_TAG],
        capture_output=True,
    )
    if check.returncode == 0:
        return True

    build = subprocess.run(
        ["docker", "build", "-t", IMAGE_TAG, SANDBOX_DIR],
        capture_output=True,
        text=True,
    )
    return build.returncode == 0


def run_in_docker(code: str, timeout: int = DOCKER_TIMEOUT_SECONDS):
    if not _ensure_sandbox_image():
        return run_in_subprocess(code, timeout=SUBPROCESS_TIMEOUT_SECONDS)

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "solution.py")
        with open(file_path, "w") as f:
            f.write(code)

        cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "256m",
            "--cpus", "0.5",
            "--pids-limit", "64",
            "-v", f"{tmpdir}:/sandbox:ro",
            "--workdir", "/sandbox",
            IMAGE_TAG,
            "python", "-m", "pytest", "solution.py", "-v", "--tb=short",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            passed = result.returncode == 0
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            return passed, output.strip(), True
        except subprocess.TimeoutExpired:
            return False, "Execution timed out inside the Docker sandbox (possible infinite loop).", True


def run_in_subprocess(code: str, timeout: int = SUBPROCESS_TIMEOUT_SECONDS):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "solution.py")
        with open(file_path, "w") as f:
            f.write(code)

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "solution.py", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env=os.environ.copy(),
            )
            passed = result.returncode == 0
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            return passed, output.strip(), False
        except subprocess.TimeoutExpired:
            return False, "Execution timed out (possible infinite loop).", False
        except FileNotFoundError:
            return False, "pytest is not installed in this environment.", False


def run_sandbox(code: str, prefer_docker: bool = True):
    """Returns (passed: bool, output: str, used_docker: bool)."""
    if prefer_docker and docker_available():
        return run_in_docker(code)
    return run_in_subprocess(code)
