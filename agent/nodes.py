"""LangGraph node implementations for the self-correcting coding agent."""

import re

from agent.llm import get_llm
from agent.state import AgentState
from sandbox.runner import run_sandbox

CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    match = CODE_BLOCK_RE.search(text)
    return match.group(1).strip() if match else text.strip()


def plan_solution(state: AgentState) -> dict:
    print("\n[Plan] Thinking through approach and edge cases...")
    llm = get_llm()
    prompt = (
        "You are a senior software engineer planning a solution before writing code.\n"
        f"Task: {state['task']}\n\n"
        "In under 150 words, outline:\n"
        "1. Your approach\n"
        "2. Edge cases to handle\n"
        "3. The test cases you will write\n"
        "Be concise. Bullet points only."
    )
    plan = llm.invoke(prompt).content
    print(plan)
    return {"plan": plan}


def generate_code(state: AgentState) -> dict:
    print("\n[Generate] Writing implementation + tests...")
    llm = get_llm()
    prompt = (
        "Write a single, self-contained Python file that:\n"
        "1. Implements a solution to the task below.\n"
        "2. Includes pytest test functions (prefixed test_) in the SAME file, "
        "covering normal cases, edge cases, and at least one adversarial case.\n\n"
        f"Task: {state['task']}\n\n"
        f"Plan:\n{state.get('plan', '')}\n\n"
        "Return ONLY a single python code block with the complete file. "
        "No prose outside the code block."
    )
    response = llm.invoke(prompt).content
    code = _extract_code(response)
    history = state.get("code_history", []) + [code]
    print(f"Code written ({len(code.splitlines())} lines)")
    return {
        "code": code,
        "code_history": history,
        "attempts": state.get("attempts", 0) + 1,
    }


def execute_and_test(state: AgentState) -> dict:
    attempt = state.get("attempts", 1)
    print(f"\n[Execute] Running tests (attempt {attempt})...")
    passed, output, used_docker = run_sandbox(state["code"])
    label = "Docker sandbox" if used_docker else "subprocess (Docker unavailable)"
    print(f"[Execute] {'PASSED' if passed else 'FAILED'}  ({label})")
    if not passed:
        print(output[-1500:])  # keep terminal output bounded
    return {"passed": passed, "test_output": output, "used_docker": used_docker}


def fix_code(state: AgentState) -> dict:
    attempt = state.get("attempts", 1)
    print(f"\n[Fix] Diagnosing failure, preparing attempt {attempt + 1}...")
    llm = get_llm()
    prompt = (
        "The following Python file (implementation + pytest tests) failed.\n\n"
        f"Task: {state['task']}\n\n"
        "Current file:\n"
        f"```python\n{state['code']}\n```\n\n"
        "Test output:\n"
        f"```\n{state['test_output'][-3000:]}\n```\n\n"
        "Fix the bug(s). Return ONLY a single corrected python code block "
        "with the complete file. No prose outside the code block."
    )
    response = llm.invoke(prompt).content
    code = _extract_code(response)
    history = state.get("code_history", []) + [code]
    return {
        "code": code,
        "code_history": history,
        "attempts": state.get("attempts", 0) + 1,
    }


def write_explanation(state: AgentState) -> dict:
    attempts = state.get("attempts", 1)
    passed = state.get("passed", False)

    if passed and attempts == 1:
        explanation = "Passed on the first attempt — no fixes were needed."
    elif passed:
        explanation = (
            f"Passed after {attempts} attempts. The agent iterated on test "
            "failures until all tests passed."
        )
    elif any(
        marker in state.get("test_output", "")
        for marker in ("No module named pytest", "pytest is not installed")
    ):
        explanation = (
            "Stopped early: the sandbox environment is missing pytest, not "
            "a bug in the generated code. Run `pip install -r requirements.txt` "
            "(or `python -m pip install pytest`) using the same Python "
            "interpreter that runs main.py, then try again."
        )
    else:
        explanation = (
            f"Did not pass within the {state.get('max_attempts', 5)}-attempt "
            "limit. See test_output and code_history for the full debugging trace."
        )

    print("\n" + "=" * 63)
    print("  RESULT")
    print("=" * 63)
    status = "✓ PASSED" if passed else "✗ FAILED"
    qualifier = "first try" if attempts == 1 and passed else f"{attempts} attempt(s)"
    print(f"  {status} — {qualifier}")
    print(explanation)

    return {"explanation": explanation}


ENVIRONMENT_ERROR_MARKERS = ("No module named pytest", "pytest is not installed")


def route_after_execute(state: AgentState) -> str:
    if state.get("passed"):
        return "done"
    if any(marker in state.get("test_output", "") for marker in ENVIRONMENT_ERROR_MARKERS):
        return "environment_error"
    if state.get("attempts", 0) >= state.get("max_attempts", 5):
        return "max_attempts"
    return "retry"
