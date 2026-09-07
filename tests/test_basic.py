"""Basic tests for vestigio — no OTEL SDK required."""

from vestigio import VestigioConfig, init_telemetry, agent_span, llm_span, tool_span
from vestigio._noop import NoOpTracer, NoOpSpan
from vestigio._spans import set_llm_usage, set_agent_output


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
