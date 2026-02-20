# AGENTS.md

Guide for agentic coding tools working in `mt-quality-management`.
This file is grounded in the repository's current executable state.

## Project Snapshot
- Stack: Python backend (`FastAPI`, `SQLAlchemy`, `Pydantic`, `pytest`).
- Entrypoint: `main.py`.
- Source root: `src/`.
- Test config: `pytest.ini`.
- Security scan config: `.bandit`.
- Dependency files: `requirements.txt`, `requirements-dev.txt`.

## Current Layout
- `main.py`: app bootstrap, middleware setup, health/readiness handlers.
- `src/utils/config.py`: settings loading via `pydantic-settings`.
- `src/utils/database.py`: engine/session utilities.
- `src/utils/security.py`: hash, JWT, and password helpers.
- `tests/`: minimal scaffold now, but pytest discovery rules are configured.

## Environment Setup
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run Commands
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
python main.py
```

## Build / Container Commands
No language-level compile step is defined. Use container build commands:
```bash
docker build -t mt-quality-management:local .
docker-compose up -d
docker-compose down
```

## Test Commands
`pytest.ini` defaults include verbose output, strict markers, warnings-as-errors,
coverage over `src`, and `--cov-fail-under=80`.

Run all tests:
```bash
pytest
```

Run one test file:
```bash
pytest tests/unit/test_document_service.py -vv
```

Run one specific test function (key single-test pattern):
```bash
pytest tests/unit/test_document_service.py::test_create_document -vv
```

Run by marker:
```bash
pytest -m security
pytest -m "not slow"
```

Debug-oriented test runs:
```bash
pytest --maxfail=1 -vv
pytest -s -vv
```

## Lint / Format / Typecheck Commands
No committed root `pyproject.toml`, `mypy.ini`, `.flake8`, or `setup.cfg` is present.
Run tools explicitly against project paths.

```bash
black main.py src tests
isort main.py src tests
flake8 main.py src tests
mypy main.py src
```

## Security Commands
```bash
bandit -c .bandit -r src
safety check
```

## Code Style Rules (Observed)

### Imports
- Group order: standard library -> third-party -> local (`src.*`).
- Separate groups with one blank line.
- Prefer absolute imports from `src`.
- Avoid wildcard imports.

### Formatting
- Follow Black-compatible formatting and 4-space indentation.
- Use clear spacing between top-level declarations (PEP 8).
- Keep text/code ASCII unless file context requires Unicode.

### Types
- Add type hints for function params and return values.
- Prefer concrete types over broad/unbounded types.
- Keep typing style consistent in the touched file.
- Avoid `Any` unless necessary and justified.

### Naming
- `snake_case`: functions, variables, modules.
- `PascalCase`: classes.
- `UPPER_SNAKE_CASE`: constants.
- Log event keys should stay stable and machine-readable.

### Error Handling
- Catch specific exceptions when possible.
- For DB transaction helpers: rollback, then re-raise.
- Never swallow exceptions silently.
- Return sanitized API responses; log detailed internal context server-side.

### Logging
- Use structured logging (`structlog`) with key/value fields.
- Include request metadata (`path`, `method`) on errors when possible.
- Never log secrets, tokens, encryption keys, or sensitive payload data.

### Security and Data
- Keep secrets only in environment/config, not source control.
- Keep JWT and encryption settings environment-driven.
- Avoid SQL string interpolation with user-controlled values.
- Include Bandit and Safety checks before final delivery.

## Testing Style Rules
- Follow pytest naming conventions: `test_*.py`, `Test*`, `test_*`.
- Use markers from `pytest.ini`: `security`, `integration`, `unit`, `contract`, `slow`, `smoke`.
- Add focused tests for changed behavior when tests exist in that area.
- Expect warnings to fail tests due to `-W error` defaults.

## Agent Workflow Checklist
1. Read nearby code and match established patterns.
2. Keep changes minimal and localized.
3. Run format/lint/typecheck on touched paths.
4. Run targeted tests first, then broader tests if available.
5. Report exact commands and outcomes.

## Cursor and Copilot Rules
- `.cursorrules`: not found.
- `.cursor/rules/`: not found.
- `.github/copilot-instructions.md`: not found.

If any of these rule files are added later, update this AGENTS.md accordingly.
