# Coding Agent

A self-correcting Python coding agent built with LangGraph. It plans a
solution, writes an implementation with pytest tests, runs the tests in an
isolated sandbox, and iterates on failures — up to 5 times — until all
tests pass.

This is the core loop behind tools like Devin and Cursor's AI editing:
**plan → generate → execute → observe → fix**.

> Built as an extension of [souvikghosh/coding-agent](https://github.com/souvikghosh/coding-agent),
> which has the same core LangGraph loop. What's different here is listed
> under [What's different](#whats-different-from-the-reference-project)
> below.

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
  └── tests fail, attempts < max ──► fix_code → execute_and_test (loop)
  │
  └── tests fail, max attempts ─────────► write_explanation → END
```

**Sandboxed execution**: generated code runs inside a disposable Docker
container with no network access, a memory/CPU cap, and a read-only mount
— the host is never touched. If Docker isn't available, it falls back to
an isolated subprocess with a timeout.

**State tracking**: every code version is kept in `code_history`, so you
can trace exactly how the agent debugged its way to the final solution.

---

## Setup

```bash
git clone <this-repo>
cd coding-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add ONE API key to .env — free options, no credit card required:
#   GROQ_API_KEY    from https://console.groq.com
#   GOOGLE_API_KEY  from https://aistudio.google.com/app/apikey
# Paid options also supported: ANTHROPIC_API_KEY, OPENAI_API_KEY
```

Docker is optional but recommended. If installed, the sandbox image is
built automatically on first run (`docker build -t coding-agent-sandbox
./sandbox`); no manual step needed.

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

These tests exercise the sandbox runner directly and need **no API key**
and **no Docker** — they hit the subprocess fallback path so they can run
in CI on every push (`.github/workflows/ci.yml`).

---

## Benchmark

`examples/benchmark.py` runs a fixed set of 5 hand-picked tasks
(easy/medium/hard) and reports `pass@1`, average fix attempts, and
per-task timing, then writes `examples/benchmark_results.json`.

This is **not** a SWE-bench or HumanEval score — it's a small, repeatable
check so changes to prompting, retry limits, or the model can be measured
against a baseline instead of judged by feel. To get a literature-
comparable number, swap `TASKS` for problems sampled from HumanEval or
SWE-bench Lite and report the result as-is, including failures.

---

## What's different from the reference project

Starting point: [souvikghosh/coding-agent](https://github.com/souvikghosh/coding-agent)
(LangGraph plan → generate → execute → fix loop, subprocess sandboxing).

Changes made here:

- **Real Docker isolation**, not just an isolated subprocess: no network
  access, memory/CPU limits, and a read-only mount, with automatic
  fallback to subprocess if Docker isn't available (`sandbox/runner.py`).
- **`write_explanation` node** that summarizes what happened — pass/fail,
  attempt count, and where to find the full debugging trace.
- **A benchmark harness** (`examples/benchmark.py`) that reports an
  honest pass@1 and average-attempts number on a fixed task set, instead
  of only ad-hoc single-task runs.
- **CI-runnable tests** (`tests/test_sandbox.py`) that need no API key,
  so the sandboxing logic is checked on every push.
- Structured as installable packages (`agent/`, `sandbox/`) rather than a
  single script, so nodes, graph wiring, and the sandbox are testable in
  isolation.

---

## Key design decisions

**Why plan before coding?** Planning forces the LLM to think about edge
cases before writing, which tends to reduce the number of fix iterations
needed — similar to how test-driven development reduces bugs.

**Why Docker over a bare subprocess?** A subprocess is isolated from the
parent process, but generated code can still read/write the filesystem
or make network calls. A container with `--network none` and resource
limits closes both of those off, at the cost of needing Docker installed
and a small per-run startup overhead.

**Why include tests in the same file?** Self-contained files are easier
to debug and iterate on — the LLM sees the implementation and its own
tests together when fixing a failure, which produces more targeted fixes.

---

## Tech stack

- **LangGraph** — execution graph with the conditional fix loop
- **LangChain** — LLM abstraction (Groq Llama, Google Gemini, Anthropic Claude, or OpenAI GPT-4o — Groq and Gemini have free tiers)
- **Docker** — sandboxed execution (network-isolated, resource-capped)
- **pytest** — test runner, both inside the sandbox and for this repo's
  own CI-safe tests
- **subprocess** — fallback sandboxing when Docker isn't available

## Known limitations

- Single-file solutions only — no multi-file projects or external
  dependencies beyond the standard library and pytest.
- The benchmark set is small (5 tasks) and hand-picked, not a standard
  benchmark; see [Benchmark](#benchmark) above.
- The LLM judge for "did it pass" is just pytest's exit code — there's no
  check for code quality, style, or efficiency beyond what the tests
  cover.
