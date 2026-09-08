# Vestigio

English Version | [中文版](README_zh.md)

Thin OTEL wrapper for agent/LLM observability.

From Latin *vestigium* — "trace, footprint." Vestigio provides agent-native instrumentation using [OpenInference](https://arize-ai.github.io/openinference/spec/) and [OTel GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) semantic conventions.

## Features

- **Three span types**: `agent_span()`, `llm_span()`, `tool_span()` — context managers with proper semantic attributes
- **Dual conventions**: Sets both OpenInference and OTel GenAI attributes for maximum backend compatibility
- **Error recording**: `set_span_error()` / `set_span_ok()` for status mapping and exception tracking
- **Session tracking**: `session_id`, `user_id`, and arbitrary `metadata` on agent spans
- **Zero overhead when disabled**: No-op stubs when OTEL SDK is not installed or telemetry is off
- **No required dependencies**: OTEL is optional (`pip install vestigio[otel]`)

## Install

```bash
pip install vestigio           # core only, spans are silent stubs
pip install vestigio[otel]     # + OTEL SDK, enables real tracing
pip install vestigio[otlp]     # + OTLP exporter for Jaeger, Tempo, etc.
```

## Quick Start

```python
from vestigio import (
    init_telemetry,
    agent_span,
    llm_span,
    tool_span,
    set_span_error,
    set_span_ok,
)
from vestigio._spans import set_llm_usage, set_agent_output

tracer = init_telemetry()

with agent_span(
    tracer,
    task="what's the weather?",
    model="gpt-4",
    session_id="sess-001",
    user_id="user-42",
    metadata={"source": "cli"},
) as root:
    with llm_span(tracer, model="gpt-4", provider="openai") as llm:
        response = call_llm(...)
        set_llm_usage(llm, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

    with tool_span(tracer, tool_name="get_weather") as tool:
        try:
            result = call_tool(...)
            set_span_ok(tool)
        except Exception as e:
            set_span_error(tool, e)

    set_agent_output(root, "The weather is sunny.")
    set_span_ok(root)
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `VESTIGIO_ENABLED` | `false` | Master switch (`1`, `true`, `yes`) |
| `VESTIGIO_ENDPOINT` | `http://localhost:4317` | OTLP endpoint |
| `VESTIGIO_CONSOLE` | `false` | Console exporter for dev |
| `OTEL_SERVICE_NAME` | `vestigio` | Standard OTEL service name |

Custom env var prefix for downstream consumers:

```python
from vestigio import VestigioConfig, init_telemetry

config = VestigioConfig.from_env(prefix="TALPA_OTEL")
tracer = init_telemetry(config=config)
```

## Compatible Backends

Any OTLP-compatible backend: Jaeger, Grafana Tempo, Arize Phoenix, Honeycomb, Datadog, etc.

## License

MIT
