"""Tests for the sandbox runner. These need no API key and no Docker —
they exercise the subprocess fallback path directly so CI can run them
without extra setup. If Docker is available, docker_available() and the
image build are exercised too.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox.runner import docker_available, run_in_subprocess, run_sandbox

PASSING_CODE = '''
def add(a, b):
    return a + b


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -1) == -2
'''

FAILING_CODE = '''
def add(a, b):
    return a - b  # bug: should be a + b


def test_add():
    assert add(2, 3) == 5
'''

TIMEOUT_CODE = '''
def test_infinite_loop():
    while True:
        pass
'''


def test_subprocess_passing_code_reports_pass():
    passed, output, used_docker = run_in_subprocess(PASSING_CODE, timeout=10)
    assert passed is True
    assert used_docker is False
    assert "2 passed" in output


def test_subprocess_failing_code_reports_fail():
    passed, output, used_docker = run_in_subprocess(FAILING_CODE, timeout=10)
    assert passed is False
    assert "assert" in output.lower()


def test_subprocess_timeout_is_caught():
    passed, output, _ = run_in_subprocess(TIMEOUT_CODE, timeout=2)
    assert passed is False
    assert "timed out" in output.lower()


def test_run_sandbox_falls_back_without_docker():
    # Even if Docker happens to be available in this environment,
    # prefer_docker=False must force the subprocess path.
    passed, output, used_docker = run_sandbox(PASSING_CODE, prefer_docker=False)
    assert passed is True
    assert used_docker is False


def test_docker_available_returns_bool():
    assert isinstance(docker_available(), bool)
