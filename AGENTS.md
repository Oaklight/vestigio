# AGENTS.md — Vestigio

> Context file for AI coding assistants. Symlinked as `CLAUDE.md`.

## What this project is

Vestigio is a thin OTEL wrapper for agent/LLM observability. It provides agent-native
instrumentation using OpenInference and OTel GenAI semantic conventions.

Part of the Oaklight ecosystem. Designed as an independent package consumed by
talpa and other agent runtimes.

## Repository Layout

```
vestigio/
├── src/vestigio/
│   ├── __init__.py        # Public API: init_telemetry(), span helpers
│   ├── _attributes.py     # Semantic attribute constants
│   ├── _config.py         # VestigioConfig, env var resolution
│   ├── _noop.py           # No-op tracer/span stubs
│   ├── _provider.py       # TracerProvider setup, exporter wiring
│   └── _spans.py          # agent_span(), llm_span(), tool_span()
├── tests/
├── .github/
│   ├── labels.yml         # GitHub label taxonomy
│   └── workflows/
│       ├── ci.yml         # Lint + test CI
│       └── release.yml    # PyPI release workflow
└── .pre-commit-config.yaml
```

## Development Setup

```bash
conda activate vestigio
pip install -e ".[dev]"
pre-commit install
```

## Key Conventions

- OTEL SDK is an optional dependency — vestigio must always be importable without it
- All `opentelemetry` imports are deferred to function bodies (never at module level)
- `_noop.py` provides zero-overhead stubs when OTEL is unavailable
- Dual attribute families: OpenInference (primary) + GenAI (secondary) on every span
- Config is env-var-driven; consumers can set a custom prefix

## CI

- Pre-commit hooks: ruff (lint + format) + ty (type check)
- GitHub Actions: lint job (pre-commit) + test job (pytest, Python 3.10–3.13)
- 100% test coverage enforced

## Git Workflow

- Use feature branches via worktree (`feature/xxx`)
- No `git add -A` — stage files explicitly
- No AI co-author tags in commits
- Conda env must be active for pre-commit hooks (ty needs it on PATH)
