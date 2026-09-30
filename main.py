"""CLI for the self-correcting coding agent.

Usage:
    python main.py "Implement binary search on a sorted list"
    python main.py --interactive
    python main.py "Write an LRU cache with get and put in O(1)" --max-attempts 3
"""

import argparse

from dotenv import load_dotenv

from agent.graph import build_graph


def run_task(task: str, max_attempts: int = 5) -> dict:
    print("=" * 63)
    print("  CODING AGENT")
    print("=" * 63)
    print(f"  Task: {task}")
    print(f"  Max fix attempts: {max_attempts}")

    graph = build_graph()
    initial_state = {
        "task": task,
        "attempts": 0,
        "max_attempts": max_attempts,
        "code_history": [],
    }
    final_state = graph.invoke(initial_state)
    return final_state


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Self-correcting coding agent")
    parser.add_argument("task", nargs="?", help="The coding task to solve")
    parser.add_argument(
        "--interactive", action="store_true", help="Run multiple tasks in a loop"
    )
    parser.add_argument(
        "--max-attempts", type=int, default=5, help="Max fix iterations (default: 5)"
    )
    args = parser.parse_args()

    if args.interactive:
        print("Interactive mode. Type 'quit' to exit.\n")
        while True:
            task = input("Task: ").strip()
            if task.lower() in ("quit", "exit", ""):
                break
            run_task(task, args.max_attempts)
            print()
    elif args.task:
        run_task(args.task, args.max_attempts)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
