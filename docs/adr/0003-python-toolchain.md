# 0003. Python toolchain

Status: Accepted
Date: 2026-11-04

## Context
The API and the worker are Python. We need a Python version, a way to install and lock packages, a linter and formatter, a type checker, a test runner and a way to load typed settings. The worker must use the `jalada` package from `apps/api` (see 0002). Every machine, continuous integration run and Docker image should install exactly the same package versions.

## Options considered

### Python version
1. **3.12.** Mature, supported until late 2028, and every library we expect to use has wheels (prebuilt packages) for it.
2. **3.13.** Newer, but a few scientific and OCR (optical character recognition) libraries lag behind on new versions.

### Package and environment manager
1. **pip with venv and pip-tools.** Built in or close to it. Three tools to combine, and locking is a separate step that is easy to forget.
2. **Poetry.** Mature lockfile and project file. Slower, does not install Python itself, and its workspace support for several packages in one repo is limited.
3. **uv.** One fast tool that installs Python, creates the virtual environment, resolves and locks packages, and supports workspaces. Younger than Poetry, made by the company behind ruff.

### Linter and formatter
1. **flake8, black and isort.** Three tools and three configurations.
2. **ruff.** One tool that lints and formats, covers the same rules, and runs much faster.

### Type checker
1. **mypy.** The reference checker, with a plugin for Pydantic.
2. **pyright.** Faster and strict, but the kickoff names mypy and its Pydantic support is weaker.

### Test runner
1. **unittest.** Built in, but verbose and class-based.
2. **pytest.** Plain functions and asserts, fixtures for fakes and databases, and a large plugin ecosystem.

### Typed settings
1. **Reading `os.environ` by hand.** No validation or types.
2. **pydantic-settings.** Reads environment variables into a typed class and fails at startup if a value is missing or wrong. FastAPI already depends on Pydantic.

## Decision
Python 3.12, uv with a workspace that holds `apps/api` and `apps/worker`, ruff for linting and formatting, mypy in strict mode with the Pydantic plugin, pytest, and pydantic-settings.

## Consequences
- One lockfile, `uv.lock`, at the repo root pins every Python package for both apps. Docker and continuous integration install from it with `uv sync --frozen`, which fails if the lockfile is out of date.
- Developers install only uv. It downloads Python 3.12 itself, pinned by a `.python-version` file.
- Strict mypy means every function needs type hints. That is more typing up front, and fewer surprises later.
- uv is young. If it stalls, Poetry or pip-tools can read the same `pyproject.toml` files with modest changes.
