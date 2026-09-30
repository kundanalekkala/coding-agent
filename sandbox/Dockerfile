# Minimal image used ONLY to execute untrusted, LLM-generated code.
# Built once and reused for every task (see runner.py / README setup).
FROM python:3.11-slim

RUN pip install --no-cache-dir pytest==8.3.3

WORKDIR /sandbox

# No CMD/ENTRYPOINT on purpose — runner.py passes the exact command
# ("python -m pytest solution.py ...") for each run.
