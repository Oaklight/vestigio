"""Vestigio — thin OTEL wrapper for agent/LLM observability.

Provides agent-native instrumentation concepts using OpenInference
and OTel GenAI semantic conventions. Zero overhead when disabled.

Usage:
    from vestigio import init_telemetry, agent_span, llm_span, tool_span

    tracer = init_telemetry()  # no-op if OTEL not installed or not enabled

    with agent_span(tracer, task="summarize this") as span:
        with llm_span(tracer, model="gpt-4") as llm:
            ...
        with tool_span(tracer, tool_name="search") as tool:
            ...
"""

__version__ = "0.1.0"

from vestigio._config import VestigioConfig
from vestigio._provider import init_telemetry, shutdown_telemetry
from vestigio._spans import agent_span, llm_span, set_span_error, set_span_ok, tool_span

__all__ = [
    "VestigioConfig",
    "agent_span",
    "init_telemetry",
    "llm_span",
    "set_span_error",
    "set_span_ok",
    "shutdown_telemetry",
    "tool_span",
]
