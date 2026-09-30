"""Wires the nodes into a LangGraph state graph.

    START
      |
      v
    plan_solution        Think through approach + edge cases
      |
      v
    generate_code        Write implementation + pytest tests
      |
      v
    execute_and_test     Run pytest in the sandbox
      |
      +-- all tests pass ------------------> write_explanation -> END
      |
      +-- fail, attempts < max --> fix_code --> execute_and_test (loop)
      |
      +-- fail, attempts == max -----------> write_explanation -> END
"""

from langgraph.graph import END, StateGraph

from agent.nodes import (
    execute_and_test,
    fix_code,
    generate_code,
    plan_solution,
    route_after_execute,
    write_explanation,
)
from agent.state import AgentState


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_solution)
    graph.add_node("generate", generate_code)
    graph.add_node("execute", execute_and_test)
    graph.add_node("fix", fix_code)
    graph.add_node("explain", write_explanation)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "generate")
    graph.add_edge("generate", "execute")
    graph.add_conditional_edges(
        "execute",
        route_after_execute,
        {
            "done": "explain",
            "retry": "fix",
            "max_attempts": "explain",
            "environment_error": "explain",
        },
    )
    graph.add_edge("fix", "execute")
    graph.add_edge("explain", END)

    return graph.compile()
