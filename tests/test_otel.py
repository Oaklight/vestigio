"""Tests with real OTEL SDK — verifies span creation and attributes."""

import builtins

import pytest

from vestigio import VestigioConfig, agent_span, init_telemetry, llm_span, tool_span
from vestigio._spans import set_agent_output, set_llm_usage

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


@pytest.fixture()
def _mock_otlp_import_error(monkeypatch):
    """Mock OTLP exporter import to raise ImportError."""
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if "otlp" in name:
            raise ImportError("no otlp")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)


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
        set_llm_usage(
            span,
            {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        )

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

    with tool_span(tracer, tool_name="get_weather", iteration=1):
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


def test_init_telemetry_default_config(monkeypatch):
    monkeypatch.delenv("VESTIGIO_ENABLED", raising=False)
    monkeypatch.delenv("VESTIGIO_ENDPOINT", raising=False)
    monkeypatch.delenv("VESTIGIO_CONSOLE", raising=False)
    tracer = init_telemetry()
    from vestigio._noop import NoOpTracer

    assert isinstance(tracer, NoOpTracer)


def test_check_otel_caching(monkeypatch):
    import vestigio._provider as prov

    monkeypatch.setattr(prov, "_HAS_OTEL", None)
    assert prov._check_otel() is True
    assert prov._HAS_OTEL is True
    assert prov._check_otel() is True


def test_init_telemetry_otel_not_installed(monkeypatch):
    import vestigio._provider as prov

    monkeypatch.setattr(prov, "_check_otel", lambda: False)
    config = VestigioConfig(enabled=True)
    tracer = init_telemetry(config=config)
    from vestigio._noop import NoOpTracer

    assert isinstance(tracer, NoOpTracer)


def test_init_telemetry_otlp_endpoint():
    config = VestigioConfig(
        enabled=True,
        endpoint="http://test:4317",
        console=False,
    )
    init_telemetry(config=config)

    from opentelemetry.sdk.trace import TracerProvider as TP

    provider = trace.get_tracer_provider()
    assert isinstance(provider, TP)


def test_init_telemetry_otlp_import_error_with_console(_mock_otlp_import_error):
    config = VestigioConfig(enabled=True, endpoint="http://x:4317", console=True)
    tracer = init_telemetry(config=config)
    assert tracer is not None


def test_init_telemetry_otlp_import_error_fallback(_mock_otlp_import_error):
    config = VestigioConfig(enabled=True, endpoint="http://x:4317", console=False)
    tracer = init_telemetry(config=config)
    assert tracer is not None


def test_shutdown_telemetry():
    from vestigio._provider import shutdown_telemetry

    config = VestigioConfig(enabled=True, console=True, endpoint="")
    init_telemetry(config=config)
    shutdown_telemetry()


def test_shutdown_telemetry_no_otel(monkeypatch):
    import vestigio._provider as prov
    from vestigio._provider import shutdown_telemetry

    monkeypatch.setattr(prov, "_check_otel", lambda: False)
    shutdown_telemetry()


def test_check_otel_import_failure(monkeypatch):
    import vestigio._provider as prov

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "opentelemetry.sdk":
            raise ImportError("no sdk")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(prov, "_HAS_OTEL", None)
    monkeypatch.setattr(builtins, "__import__", mock_import)
    assert prov._check_otel() is False
    assert prov._HAS_OTEL is False


def test_init_telemetry_otlp_success(monkeypatch):
    from unittest.mock import MagicMock

    real_import = builtins.__import__

    mock_exporter_cls = MagicMock()

    def mock_import(name, *args, **kwargs):
        if "otlp" in name:
            mod = MagicMock()
            mod.OTLPSpanExporter = mock_exporter_cls
            return mod
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    config = VestigioConfig(enabled=True, endpoint="http://collector:4317", console=False)
    tracer = init_telemetry(config=config)
    assert tracer is not None
    mock_exporter_cls.assert_called_once_with(endpoint="http://collector:4317")


def test_set_span_error(otel_setup):
    from vestigio._spans import set_span_error

    tracer, exporter = otel_setup

    with agent_span(tracer, task="fail") as span:
        err = ValueError("something broke")
        set_span_error(span, err)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    s = spans[0]
    assert s.status.status_code.name == "ERROR"
    assert "something broke" in s.status.description
    events = s.events
    assert any(e.name == "exception" for e in events)


def test_set_span_ok(otel_setup):
    from vestigio._spans import set_span_ok

    tracer, exporter = otel_setup

    with agent_span(tracer, task="succeed") as span:
        set_span_ok(span)

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "OK"


def test_set_span_error_in_agent_span(otel_setup):
    from vestigio._spans import set_span_error

    tracer, exporter = otel_setup

    with agent_span(tracer, task="will fail", model="gpt-4") as span:
        try:
            raise RuntimeError("tool call failed")
        except RuntimeError as exc:
            set_span_error(span, exc)

    spans = exporter.get_finished_spans()
    s = spans[0]
    attrs = dict(s.attributes)
    assert attrs["openinference.span.kind"] == "AGENT"
    assert s.status.status_code.name == "ERROR"
    assert "tool call failed" in s.status.description
    exc_events = [e for e in s.events if e.name == "exception"]
    assert len(exc_events) == 1
    exc_attrs = dict(exc_events[0].attributes)
    assert exc_attrs["exception.type"] == "RuntimeError"
    assert exc_attrs["exception.message"] == "tool call failed"
