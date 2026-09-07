"""TracerProvider setup and lifecycle.

All opentelemetry imports are deferred to function bodies so that
importing vestigio never fails, even without OTEL installed.
"""

from __future__ import annotations

import logging
from typing import Any

from vestigio._config import VestigioConfig
from vestigio._noop import NoOpTracer, get_noop_tracer

logger = logging.getLogger(__name__)

_HAS_OTEL: bool | None = None


def _check_otel() -> bool:
    """Check if opentelemetry SDK is importable. Cached."""
    global _HAS_OTEL
    if _HAS_OTEL is None:
        try:
            import opentelemetry.sdk  # noqa: F401

            _HAS_OTEL = True
        except ImportError:
            _HAS_OTEL = False
    return _HAS_OTEL


def init_telemetry(
    config: VestigioConfig | None = None,
) -> Any:
    """Initialize OTEL tracing and return a Tracer.

    Returns a real OTEL Tracer if enabled and SDK is available,
    otherwise returns a NoOpTracer.

    Args:
        config: Telemetry config. If None, resolves from env vars.

    Returns:
        A Tracer instance (real or no-op).
    """
    if config is None:
        config = VestigioConfig.from_env()

    if not config.enabled:
        logger.debug("Telemetry disabled")
        return get_noop_tracer()

    if not _check_otel():
        logger.warning(
            "OTEL SDK not installed — telemetry disabled. "
            "Install with: pip install vestigio[otel]"
        )
        return get_noop_tracer()

    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    resource = Resource.create({"service.name": config.service_name})
    provider = TracerProvider(resource=resource)

    if config.console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("Console span exporter enabled")

    if config.endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=config.endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP exporter enabled: %s", config.endpoint)
        except ImportError:
            if not config.console:
                logger.warning(
                    "OTLP exporter not available — install vestigio[otlp]. "
                    "Falling back to console exporter."
                )
                provider.add_span_processor(
                    BatchSpanProcessor(ConsoleSpanExporter())
                )

    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("vestigio", __import__("vestigio").__version__)
    logger.info("Telemetry initialized: service=%s", config.service_name)
    return tracer


def shutdown_telemetry() -> None:
    """Flush and shut down the tracer provider."""
    if not _check_otel():
        return

    from opentelemetry import trace

    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()
        logger.debug("Tracer provider shut down")
