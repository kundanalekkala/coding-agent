# Coding Agent

[![CI](https://github.com/kundanalekkala/coding-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/kundanalekkala/coding-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![LangGraph](https://img.shields.io/badge/built%20with-LangGraph-green)

A self-correcting Python coding agent built with LangGraph. It plans a solution, writes an implementation with pytest tests, runs them in an isolated sandbox, and iterates on failures (up to 5 times) until all tests pass.

This is the core loop behind tools like Devin and Cursor's AI editing: **plan → generate → execute → observe → fix**.

---

## Features

- **Plan-first generation:** the agent reasons about the approach and edge cases before writing code.
- **Self-correcting loop:** failed tests feed back into a fix step, up to 5 attempts.
- **Real Docker isolation:** no network, memory/CPU limits, read-only mount, with automatic subprocess fallback (`sandbox/runner.py`).
- **Explanation node:** `write_explanation` summarizes pass/fail, attempt count, and where to find the debugging trace.
- **Full code history:** every version is stored in `code_history`.
- **Benchmark harness:** reports pass@1 and average attempts on a fixed task set.
- **CI-safe tests:** sandbox tests need no API key or Docker.
- **Multi-provider:** Groq, Gemini (both free tiers), Claude, or GPT-4o.

---

## How it works

```
START
  │
  ▼
plan_solution          Think through the approach and edge cases before coding
  │
  ▼
generate_code          Write implementation + pytest tests in one file
  │
  ▼
execute_and_test       Run pytest inside the sandbox
  │
  ├── all tests pass ──────────────────────► write_explanation → END
  │
  ├── tests fail, attempts < max ──► fix_code → execute_and_test (loop)
  │
  └── tests fail, max attempts ────────────► write_explanation → END
```

**Sandboxed execution:** generated code runs in a disposable Docker container with no network access, memory/CPU caps, and a read-only mount, so the host is never touched. If Docker isn't available, it falls back to an isolated subprocess with a timeout.

**State tracking:** every code version is kept in `code_history`, so you can trace how the agent debugged its way to the final solution.

---

## Project structure

```
coding-agent/
├── agent/          # LangGraph nodes and graph wiring
├── sandbox/        # Docker + subprocess runner, sandbox Dockerfile
├── examples/       # demo_tasks.py, benchmark.py
├── tests/          # CI-safe sandbox tests (no API key needed)
├── .github/workflows/
├── main.py         # CLI entry point
└── requirements.txt
```

---

## Setup

```bash
git clone https://github.com/kundanalekkala/coding-agent.git
cd coding-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add **one** API key to `.env`:

| Provider | Variable | Cost |
|---|---|---|
| Groq (Llama) | `GROQ_API_KEY` | Free, from [console.groq.com](https://console.groq.com) |
| Google Gemini | `GOOGLE_API_KEY` | Free, from [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Anthropic Claude | `ANTHROPIC_API_KEY` | Paid |
| OpenAI GPT-4o | `OPENAI_API_KEY` | Paid |

Docker is optional but recommended. If installed, the sandbox image is built automatically on first run (`docker build -t coding-agent-sandbox ./sandbox`).

---

## Usage

```bash
# Single task
python main.py "Implement binary search on a sorted list"
python main.py "Write an LRU cache with get and put in O(1)"

# Interactive mode
python main.py --interactive

# Demo: 3 tasks of increasing difficulty
python examples/demo_tasks.py

# Benchmark: 5 fixed tasks, reports pass@1 and avg attempts
python examples/benchmark.py
```

### Example output

```
═══════════════════════════════════════════════════════════
  CODING AGENT
═══════════════════════════════════════════════════════════
  Task: Implement binary search on a sorted list
  Max fix attempts: 5

[Plan]
  • Function takes a sorted list and target value
  • Return index if found, -1 if not
  • Handle empty list edge case
  • Use left/right pointers, check midpoint each iteration

[Generate] Code written (38 lines)
[Execute] Running tests (attempt 1)...  (Docker sandbox)
[Execute] PASSED

═══════════════════════════════════════════════════════════
  RESULT
═══════════════════════════════════════════════════════════
  ✓ PASSED — first try
```

---

## Running the tests

```bash
pytest tests/ -v
```

These tests exercise the sandbox runner directly and need **no API key** and **no Docker** (they use the subprocess fallback), so they run in CI on every push.

---

## Benchmark

`examples/benchmark.py` runs 5 hand-picked tasks (easy/medium/hard), reports `pass@1`, average fix attempts, and per-task timing, then writes `examples/benchmark_results.json`.

This is **not** a SWE-bench or HumanEval score. It's a small, repeatable baseline so changes to prompting, retry limits, or the model can be measured instead of judged by feel. For a literature-comparable number, swap `TASKS` for problems sampled from HumanEval or SWE-bench Lite and report results as-is, including failures.

---

## Key design decisions

**Why plan before coding?** Planning forces the LLM to consider edge cases up front, which tends to reduce fix iterations, much like test-driven development reduces bugs.

**Why Docker over a bare subprocess?** A subprocess is isolated from the parent process, but generated code can still touch the filesystem or network. A container with `--network none` and resource limits closes both off, at the cost of needing Docker and a small startup overhead.

**Why tests in the same file?** The LLM sees the implementation and its tests together when fixing a failure, which produces more targeted fixes.

---

## Tech stack

- **LangGraph:** execution graph with the conditional fix loop
- **LangChain:** LLM abstraction
- **Docker:** network-isolated, resource-capped sandbox
- **pytest:** test runner, inside the sandbox and for the repo's own tests
- **subprocess:** fallback sandboxing

---

## Known limitations

- Single-file solutions only: no multi-file projects or dependencies beyond the standard library and pytest.
- The benchmark is small (5 tasks) and hand-picked, not a standard benchmark.
- "Passed" means pytest's exit code is 0. There's no check for code quality, style, or efficiency beyond what the tests cover.

---

## Roadmap

- Multi-file project support
- Run benchmarks on HumanEval / SWE-bench Lite subsets
- Static analysis (lint/type checks) as an extra pass criterion

## License

Add a LICENSE file (MIT is a common choice) and reference it here.
