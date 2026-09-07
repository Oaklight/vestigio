# Vestigio

Thin OTEL wrapper for agent/LLM observability.

From Latin *vestigium* — "trace, footprint." Vestigio provides agent-native instrumentation using [OpenInference](https://arize-ai.github.io/openinference/spec/) and [OTel GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) semantic conventions.

## Features

- **Three span types**: `agent_span()`, `llm_span()`, `tool_span()` — context managers with proper semantic attributes
- **Dual conventions**: Sets both OpenInference and OTel GenAI attributes for maximum backend compatibility
- **Zero overhead when disabled**: No-op stubs when OTEL SDK is not installed or telemetry is off
- **Env-var config**: `VESTIGIO_ENABLED`, `VESTIGIO_ENDPOINT`, `VESTIGIO_CONSOLE`
- **No required dependencies**: OTEL is optional (`pip install vestigio[otel]`)

## Install

```bash
pip install vestigio           # core (no-op without OTEL)
pip install vestigio[otel]     # with OTEL SDK + console exporter
pip install vestigio[otlp]     # with OTLP gRPC exporter (Jaeger, Tempo, etc.)
```

## Quick Start

```python
from vestigio import init_telemetry, agent_span, llm_span, tool_span, set_llm_usage

tracer = init_telemetry()

with agent_span(tracer, task="what's the weather?", model="gpt-4") as root:
    with llm_span(tracer, model="gpt-4", provider="openai") as llm:
        response = call_llm(...)
        set_llm_usage(llm, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

    with tool_span(tracer, tool_name="get_weather") as tool:
        result = call_tool(...)

    with llm_span(tracer, model="gpt-4", provider="openai", iteration=1) as llm:
        final = call_llm(...)
        set_llm_usage(llm, usage)
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `VESTIGIO_ENABLED` | `false` | Master switch (`1`, `true`, `yes`) |
| `VESTIGIO_ENDPOINT` | `http://localhost:4317` | OTLP endpoint |
| `VESTIGIO_CONSOLE` | `false` | Console exporter for dev |
| `OTEL_SERVICE_NAME` | `vestigio` | Standard OTEL service name |

Consumers can use a custom env var prefix:
```python
from vestigio import VestigioConfig, init_telemetry

config = VestigioConfig.from_env(prefix="TALPA_OTEL")
tracer = init_telemetry(config=config)
```

## Compatible Backends

Any OTLP-compatible backend: Jaeger, Grafana Tempo, Arize Phoenix, Honeycomb, Datadog, etc.

## License

MIT
