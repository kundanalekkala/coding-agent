"""A small, honest benchmark for the agent.

This is NOT a claim of SWE-bench or HumanEval performance — it's a fixed
set of hand-picked tasks so you can track whether changes to the agent
(prompting, retry limits, model choice) help or hurt, and so you have a
real number to put in a README instead of "it seems to work."

For an actual literature-comparable number, point EXTRA_TASKS at problems
sampled from HumanEval or SWE-bench Lite yourself and re-run.

Usage:
    python examples/benchmark.py
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from main import run_task

TASKS = [
    {"id": "easy_1", "task": "Implement binary search on a sorted list."},
    {"id": "easy_2", "task": "Write a function that checks whether a string is a palindrome, ignoring case and non-alphanumeric characters."},
    {"id": "medium_1", "task": "Write an LRU cache class with get(key) and put(key, value) in O(1) time."},
    {"id": "medium_2", "task": "Given a list of intervals, merge all overlapping intervals and return the result sorted by start time."},
    {"id": "hard_1", "task": "Implement a function that finds the longest increasing subsequence in a list of integers and returns its length."},
]


def main():
    load_dotenv()
    results = []

    for item in TASKS:
        start = time.time()
        state = run_task(item["task"], max_attempts=5)
        elapsed = round(time.time() - start, 1)
        results.append(
            {
                "id": item["id"],
                "task": item["task"],
                "passed": state.get("passed", False),
                "attempts": state.get("attempts"),
                "used_docker": state.get("used_docker"),
                "seconds": elapsed,
            }
        )
        print("\n")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    avg_attempts = sum(r["attempts"] or 0 for r in results) / total

    summary = {
        "pass_at_1": round(passed / total, 3),
        "passed": passed,
        "total": total,
        "avg_attempts": round(avg_attempts, 2),
        "results": results,
    }

    print("=" * 63)
    print("  BENCHMARK SUMMARY")
    print("=" * 63)
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']:<10} attempts={r['attempts']}  {r['seconds']}s")
    print(f"\n  pass@1: {summary['pass_at_1']*100:.1f}%  ({passed}/{total})")
    print(f"  avg attempts: {summary['avg_attempts']}")

    out_path = Path(__file__).resolve().parent / "benchmark_results.json"
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\n  Full results written to {out_path}")


if __name__ == "__main__":
    main()
