"""Shared state passed between LangGraph nodes."""

from typing import List, TypedDict


class AgentState(TypedDict, total=False):
    # Input
    task: str
    max_attempts: int

    # Working state
    plan: str
    code: str
    code_history: List[str]
    test_output: str
    passed: bool
    attempts: int
    used_docker: bool

    # Output
    explanation: str
