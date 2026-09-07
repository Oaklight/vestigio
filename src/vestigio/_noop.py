"""No-op tracer and span stubs.

Used when OTEL SDK is not installed or telemetry is disabled.
Zero overhead — no external dependencies.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


class NoOpSpan:
    """Span stub that silently discards all operations."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any, description: str | None = None) -> None:
        pass

    def record_exception(self, exception: BaseException) -> None:
        pass

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self) -> NoOpSpan:
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class NoOpTracer:
    """Tracer stub that returns NoOpSpans."""

    @contextmanager
    def start_as_current_span(
        self, name: str, **kwargs: Any
    ) -> Iterator[NoOpSpan]:
        yield NoOpSpan()

    def start_span(self, name: str, **kwargs: Any) -> NoOpSpan:
        return NoOpSpan()


_NOOP_TRACER = NoOpTracer()


def get_noop_tracer() -> NoOpTracer:
    """Return the singleton no-op tracer."""
    return _NOOP_TRACER
