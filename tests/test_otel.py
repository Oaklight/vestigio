"""Tests with real OTEL SDK — verifies span creation and attributes."""

import pytest

from vestigio import VestigioConfig, init_telemetry, agent_span, llm_span, tool_span
from vestigio._spans import set_llm_usage, set_agent_output

pytest.importorskip("opentelemetry.sdk")

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture(autouse=True)
def _reset_tracer_provider():
    """Reset global tracer provider between tests."""
    yield
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE._done = False


@pytest.fixture()
def otel_setup():
    """Set up an in-memory exporter for capturing spans."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("test")
    yield tracer, exporter
    provider.shutdown()


def test_agent_span_attributes(otel_setup):
    tracer, exporter = otel_setup

    with agent_span(tracer, task="hello world", agent_name="talpa", model="gpt-4") as span:
        set_agent_output(span, "goodbye")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    s = spans[0]
    assert s.name == "agent"
    attrs = dict(s.attributes)
    assert attrs["openinference.span.kind"] == "AGENT"
    assert attrs["agent.name"] == "talpa"
    assert attrs["gen_ai.agent.name"] == "talpa"
    assert attrs["input.value"] == "hello world"
    assert attrs["output.value"] == "goodbye"
    assert attrs["llm.model_name"] == "gpt-4"
    assert attrs["gen_ai.request.model"] == "gpt-4"


def test_llm_span_with_usage(otel_setup):
    tracer, exporter = otel_setup

    with llm_span(tracer, model="claude-4", provider="anthropic", iteration=2) as span:
        set_llm_usage(span, {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        })

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    attrs = dict(spans[0].attributes)
    assert attrs["openinference.span.kind"] == "LLM"
    assert attrs["llm.model_name"] == "claude-4"
    assert attrs["gen_ai.request.model"] == "claude-4"
    assert attrs["llm.system"] == "anthropic"
    assert attrs["gen_ai.provider.name"] == "anthropic"
    assert attrs["llm.token_count.prompt"] == 100
    assert attrs["llm.token_count.completion"] == 50
    assert attrs["llm.token_count.total"] == 150
    assert attrs["gen_ai.usage.input_tokens"] == 100
    assert attrs["gen_ai.usage.output_tokens"] == 50
    assert attrs["llm.iteration"] == 2


def test_tool_span_single(otel_setup):
    tracer, exporter = otel_setup

    with tool_span(tracer, tool_name="get_weather", iteration=1) as span:
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    attrs = dict(spans[0].attributes)
    assert spans[0].name == "get_weather"
    assert attrs["openinference.span.kind"] == "TOOL"
    assert attrs["tool.name"] == "get_weather"
    assert attrs["gen_ai.tool.name"] == "get_weather"
    assert attrs["tool.count"] == 1


def test_tool_span_batch(otel_setup):
    tracer, exporter = otel_setup

    with tool_span(tracer, tool_names=["search", "fetch", "parse"], iteration=3):
        pass

    spans = exporter.get_finished_spans()
    attrs = dict(spans[0].attributes)
    assert "search, fetch, parse" == attrs["tool.name"]
    assert attrs["tool.count"] == 3


def test_nested_spans(otel_setup):
    tracer, exporter = otel_setup

    with agent_span(tracer, task="test") as root:
        with llm_span(tracer, model="gpt-4", iteration=0):
            pass
        with tool_span(tracer, tool_name="search", iteration=1):
            pass
        with llm_span(tracer, model="gpt-4", iteration=1):
            pass
        set_agent_output(root, "done")

    spans = exporter.get_finished_spans()
    assert len(spans) == 4

    agent_s = [s for s in spans if s.name == "agent"][0]
    children = [s for s in spans if s.parent and s.parent.span_id == agent_s.context.span_id]
    assert len(children) == 3


def test_init_telemetry_with_console(monkeypatch):
    monkeypatch.setenv("VESTIGIO_ENABLED", "1")
    monkeypatch.setenv("VESTIGIO_CONSOLE", "1")
    monkeypatch.setenv("VESTIGIO_ENDPOINT", "")

    config = VestigioConfig.from_env()
    tracer = init_telemetry(config=config)
    assert not isinstance(tracer, type(None))

    from opentelemetry.sdk.trace import TracerProvider
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)
