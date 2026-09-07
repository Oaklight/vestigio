"""Span context managers for agent/LLM/tool tracing.

These are the primary API for consumers. Each returns a context
manager that creates a properly attributed span following
OpenInference + GenAI semantic conventions.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from vestigio._attributes import GenAI, OpenInference
from vestigio._noop import NoOpSpan, NoOpTracer

# Type alias — works with both real OTEL Tracer and NoOpTracer
TracerLike = Any


@contextmanager
def agent_span(
    tracer: TracerLike,
    *,
    task: str = "",
    agent_name: str = "agent",
    model: str = "",
    session_id: str = "",
    user_id: str = "",
    metadata: dict[str, str] | None = None,
) -> Iterator[Any]:
    """Create an AGENT span (typically the root span for one chat turn).

    Args:
        tracer: Tracer instance (real or no-op).
        task: User input / task description. Set as input.value.
        agent_name: Agent identifier.
        model: Model name, if known at start time.
        session_id: Session/conversation identifier for trace grouping.
        user_id: User identifier.
        metadata: Arbitrary key-value pairs set as metadata.{key} attributes.

    Yields:
        The span object. Caller can set additional attributes or
        record the output before exiting.
    """
    if isinstance(tracer, NoOpTracer):
        yield NoOpSpan()
        return

    with tracer.start_as_current_span("agent") as span:
        span.set_attribute(OpenInference.SPAN_KIND, OpenInference.SpanKind.AGENT)
        span.set_attribute(OpenInference.AGENT_NAME, agent_name)
        span.set_attribute(GenAI.AGENT_NAME, agent_name)
        if task:
            span.set_attribute(OpenInference.INPUT_VALUE, task)
        if model:
            span.set_attribute(OpenInference.LLM_MODEL_NAME, model)
            span.set_attribute(GenAI.REQUEST_MODEL, model)
        if session_id:
            span.set_attribute(OpenInference.SESSION_ID, session_id)
            span.set_attribute(GenAI.CONVERSATION_ID, session_id)
        if user_id:
            span.set_attribute(OpenInference.USER_ID, user_id)
        if metadata:
            for key, value in metadata.items():
                span.set_attribute(f"metadata.{key}", value)
        yield span


@contextmanager
def llm_span(
    tracer: TracerLike,
    *,
    model: str = "",
    provider: str = "",
    iteration: int = 0,
) -> Iterator[Any]:
    """Create an LLM span for one LLM call.

    Args:
        tracer: Tracer instance (real or no-op).
        model: Model name.
        provider: LLM provider name.
        iteration: Tool-loop iteration index.

    Yields:
        The span object. Caller should set usage attributes
        (via set_llm_usage) after the call completes.
    """
    if isinstance(tracer, NoOpTracer):
        yield NoOpSpan()
        return

    with tracer.start_as_current_span(f"llm.call.{iteration}") as span:
        span.set_attribute(OpenInference.SPAN_KIND, OpenInference.SpanKind.LLM)
        span.set_attribute(GenAI.OPERATION_NAME, "chat")
        if model:
            span.set_attribute(OpenInference.LLM_MODEL_NAME, model)
            span.set_attribute(GenAI.REQUEST_MODEL, model)
        if provider:
            span.set_attribute(OpenInference.LLM_SYSTEM, provider)
            span.set_attribute(GenAI.PROVIDER_NAME, provider)
        span.set_attribute("llm.iteration", iteration)
        yield span


@contextmanager
def tool_span(
    tracer: TracerLike,
    *,
    tool_name: str = "",
    tool_names: list[str] | None = None,
    iteration: int = 0,
) -> Iterator[Any]:
    """Create a TOOL span for tool execution.

    Supports both single tool and batch tool calls. For batches,
    the span name uses "tools.batch" and all names are recorded.

    Args:
        tracer: Tracer instance (real or no-op).
        tool_name: Single tool name.
        tool_names: List of tool names (for batch execution).
        iteration: Tool-loop iteration index.

    Yields:
        The span object.
    """
    if isinstance(tracer, NoOpTracer):
        yield NoOpSpan()
        return

    names = tool_names or ([tool_name] if tool_name else [])
    label = names[0] if len(names) == 1 else f"tools.batch.{iteration}"

    with tracer.start_as_current_span(label) as span:
        span.set_attribute(OpenInference.SPAN_KIND, OpenInference.SpanKind.TOOL)
        if names:
            joined = ", ".join(names)
            span.set_attribute(OpenInference.TOOL_NAME, joined)
            span.set_attribute(GenAI.TOOL_NAME, joined)
        span.set_attribute("tool.iteration", iteration)
        span.set_attribute("tool.count", len(names))
        yield span


def set_llm_usage(span: Any, usage: dict[str, Any] | None) -> None:
    """Set token usage attributes on an LLM span.

    Args:
        span: The LLM span to annotate.
        usage: Usage dict with prompt_tokens, completion_tokens,
            total_tokens keys (as returned by LLM clients).
    """
    if usage is None or isinstance(span, NoOpSpan):
        return

    prompt = usage.get("prompt_tokens", 0)
    completion = usage.get("completion_tokens", 0)
    total = usage.get("total_tokens", 0)

    # OpenInference
    span.set_attribute(OpenInference.LLM_TOKEN_COUNT_PROMPT, prompt)
    span.set_attribute(OpenInference.LLM_TOKEN_COUNT_COMPLETION, completion)
    span.set_attribute(OpenInference.LLM_TOKEN_COUNT_TOTAL, total)

    # GenAI
    span.set_attribute(GenAI.USAGE_INPUT_TOKENS, prompt)
    span.set_attribute(GenAI.USAGE_OUTPUT_TOKENS, completion)


def set_agent_output(span: Any, output: str) -> None:
    """Set the output value on an agent span.

    Args:
        span: The agent span to annotate.
        output: Final text output from the agent.
    """
    if isinstance(span, NoOpSpan) or not output:
        return
    span.set_attribute(OpenInference.OUTPUT_VALUE, output)


def set_span_error(span: Any, exception: BaseException) -> None:
    """Record an exception and set ERROR status on a span.

    Args:
        span: The span to mark as errored.
        exception: The exception that occurred.
    """
    if isinstance(span, NoOpSpan):
        return

    span.record_exception(exception)
    try:
        from opentelemetry.trace import StatusCode

        span.set_status(StatusCode.ERROR, str(exception))
    except ImportError:
        span.set_attribute("otel.status_code", "ERROR")
        span.set_attribute("error.message", str(exception))


def set_span_ok(span: Any) -> None:
    """Set OK status on a span.

    Args:
        span: The span to mark as successful.
    """
    if isinstance(span, NoOpSpan):
        return

    try:
        from opentelemetry.trace import StatusCode

        span.set_status(StatusCode.OK)
    except ImportError:
        span.set_attribute("otel.status_code", "OK")
