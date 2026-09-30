"""Runs 3 tasks of increasing difficulty to showcase the agent end-to-end."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from main import run_task

TASKS = [
    "Implement binary search on a sorted list.",
    "Write an LRU cache class with get(key) and put(key, value) in O(1) time.",
    "Given a list of intervals, merge all overlapping intervals and return the result sorted.",
]

if __name__ == "__main__":
    load_dotenv()
    for task in TASKS:
        run_task(task)
        print("\n")
