"""Basic tests for vestigio — no OTEL SDK required."""

from vestigio import VestigioConfig, agent_span, init_telemetry, llm_span, tool_span
from vestigio._noop import NoOpSpan, NoOpTracer
from vestigio._spans import set_agent_output, set_llm_usage


def test_import():
    """Package is importable."""
    import vestigio

    assert vestigio.__version__ == "0.1.0"


def test_config_defaults():
    config = VestigioConfig()
    assert not config.enabled
    assert config.endpoint == "http://localhost:4317"
    assert config.service_name == "vestigio"
    assert not config.console


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("VESTIGIO_ENABLED", "1")
    monkeypatch.setenv("VESTIGIO_ENDPOINT", "http://jaeger:4317")
    monkeypatch.setenv("VESTIGIO_CONSOLE", "true")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-agent")

    config = VestigioConfig.from_env()
    assert config.enabled
    assert config.endpoint == "http://jaeger:4317"
    assert config.service_name == "my-agent"
    assert config.console


def test_config_custom_prefix(monkeypatch):
    monkeypatch.setenv("TALPA_OTEL_ENABLED", "yes")
    config = VestigioConfig.from_env(prefix="TALPA_OTEL")
    assert config.enabled


def test_disabled_returns_noop():
    tracer = init_telemetry(config=VestigioConfig(enabled=False))
    assert isinstance(tracer, NoOpTracer)


def test_noop_spans():
    tracer = NoOpTracer()

    with agent_span(tracer, task="hello") as span:
        assert isinstance(span, NoOpSpan)
        span.set_attribute("key", "value")
        span.add_event("test")

    with llm_span(tracer, model="gpt-4") as span:
        assert isinstance(span, NoOpSpan)
        set_llm_usage(span, {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

    with tool_span(tracer, tool_name="search") as span:
        assert isinstance(span, NoOpSpan)


def test_set_agent_output_noop():
    span = NoOpSpan()
    set_agent_output(span, "some output")


def test_noop_batch_tool_span():
    tracer = NoOpTracer()
    with tool_span(tracer, tool_names=["a", "b", "c"], iteration=2) as span:
        assert isinstance(span, NoOpSpan)


def test_noop_span_full_api():
    span = NoOpSpan()
    span.set_status("OK")
    span.set_status("ERROR", description="boom")
    span.record_exception(RuntimeError("test"))
    span.add_event("evt", attributes={"k": "v"})
    span.end()
    with span:
        pass


def test_noop_tracer_start_span():
    tracer = NoOpTracer()
    span = tracer.start_span("manual")
    assert isinstance(span, NoOpSpan)


def test_get_noop_tracer_singleton():
    from vestigio._noop import get_noop_tracer

    t1 = get_noop_tracer()
    t2 = get_noop_tracer()
    assert t1 is t2
    assert isinstance(t1, NoOpTracer)


def test_noop_tracer_start_as_current_span():
    tracer = NoOpTracer()
    with tracer.start_as_current_span("direct") as span:
        assert isinstance(span, NoOpSpan)


def test_set_span_error_noop():
    from vestigio._spans import set_span_error

    span = NoOpSpan()
    set_span_error(span, RuntimeError("boom"))


def test_set_span_ok_noop():
    from vestigio._spans import set_span_ok

    span = NoOpSpan()
    set_span_ok(span)


def test_set_span_error_no_otel(monkeypatch):
    import builtins
    from unittest.mock import MagicMock

    from vestigio._spans import set_span_error

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "opentelemetry.trace":
            raise ImportError("no otel")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    span = MagicMock()
    set_span_error(span, RuntimeError("fail"))
    span.record_exception.assert_called_once()
    span.set_attribute.assert_any_call("otel.status_code", "ERROR")
    span.set_attribute.assert_any_call("error.message", "fail")


def test_set_span_ok_no_otel(monkeypatch):
    import builtins
    from unittest.mock import MagicMock

    from vestigio._spans import set_span_ok

    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "opentelemetry.trace":
            raise ImportError("no otel")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    span = MagicMock()
    set_span_ok(span)
    span.set_attribute.assert_called_once_with("otel.status_code", "OK")


def test_agent_span_with_session_metadata_noop():
    tracer = NoOpTracer()
    with agent_span(
        tracer,
        task="test",
        session_id="sess-123",
        user_id="user-456",
        metadata={"env": "dev", "version": "1.0"},
    ) as span:
        assert isinstance(span, NoOpSpan)
