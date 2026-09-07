"""Semantic attribute constants for OpenInference and OTel GenAI conventions.

Centralizes all attribute keys so instrumentation code uses constants
instead of string literals. Covers the subset relevant to agent/LLM/tool
tracing — not an exhaustive mirror of either spec.

References:
    OpenInference: https://arize-ai.github.io/openinference/spec/
    OTel GenAI: https://opentelemetry.io/docs/specs/semconv/gen-ai/
"""


# ── OpenInference ──


class OpenInference:
    """OpenInference semantic convention attribute keys."""

    SPAN_KIND = "openinference.span.kind"

    # Span kind values
    class SpanKind:
        AGENT = "AGENT"
        LLM = "LLM"
        TOOL = "TOOL"
        CHAIN = "CHAIN"

    # Agent
    AGENT_NAME = "agent.name"

    # LLM
    LLM_SYSTEM = "llm.system"
    LLM_MODEL_NAME = "llm.model_name"
    LLM_INVOCATION_PARAMS = "llm.invocation_parameters"
    LLM_TOKEN_COUNT_PROMPT = "llm.token_count.prompt"
    LLM_TOKEN_COUNT_COMPLETION = "llm.token_count.completion"
    LLM_TOKEN_COUNT_TOTAL = "llm.token_count.total"

    # Tool
    TOOL_NAME = "tool.name"
    TOOL_DESCRIPTION = "tool.description"

    # Generic I/O
    INPUT_VALUE = "input.value"
    INPUT_MIME_TYPE = "input.mime_type"
    OUTPUT_VALUE = "output.value"
    OUTPUT_MIME_TYPE = "output.mime_type"

    # Session
    SESSION_ID = "session.id"
    USER_ID = "user.id"


class GenAI:
    """OTel GenAI semantic convention attribute keys (forward compat)."""

    REQUEST_MODEL = "gen_ai.request.model"
    RESPONSE_MODEL = "gen_ai.response.model"
    PROVIDER_NAME = "gen_ai.provider.name"
    OPERATION_NAME = "gen_ai.operation.name"

    # Token usage
    USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
    USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"

    # Tool
    TOOL_NAME = "gen_ai.tool.name"
    TOOL_CALL_ID = "gen_ai.tool.call.id"

    # Agent
    AGENT_NAME = "gen_ai.agent.name"
