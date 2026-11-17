# devsecops-lab

Assignment 9 (Software Maintenance) – Practicing DevSecOps Fundamentals.

A tiny Flask notes service. The first commit contains **intentional** security and
quality problems so the checks have something to find. All secrets in this repo are
fake demo values.

| Check | Tool | Where |
|---|---|---|
| Lint / static analysis | flake8 + flake8-bandit | `.github/workflows/ci.yml` (`lint` job) |
| Unit tests | pytest | `.github/workflows/ci.yml` (`test` job) |

Run locally:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/flake8 src/ tests/
.venv/bin/pytest
```

Author: 張晏榕
