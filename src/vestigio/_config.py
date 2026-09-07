"""Vestigio configuration — env-var-driven."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class VestigioConfig:
    """Telemetry configuration resolved from environment variables.

    Attributes:
        enabled: Master switch. Set VESTIGIO_ENABLED=1 to activate.
        endpoint: OTLP endpoint. Defaults to localhost:4317.
        service_name: OTEL service name. Defaults to "vestigio".
        console: Enable console exporter for dev. Set VESTIGIO_CONSOLE=1.
    """

    enabled: bool = False
    endpoint: str = "http://localhost:4317"
    service_name: str = "vestigio"
    console: bool = False

    @classmethod
    def from_env(cls, *, prefix: str = "VESTIGIO") -> VestigioConfig:
        """Resolve config from environment variables.

        Env vars checked (with default prefix "VESTIGIO"):
            {prefix}_ENABLED — "1" or "true" to enable
            {prefix}_ENDPOINT — OTLP endpoint URL
            {prefix}_CONSOLE — "1" or "true" for console exporter
            OTEL_SERVICE_NAME — standard OTEL service name

        Args:
            prefix: Env var prefix. Consumers can override to use
                their own namespace (e.g. "TALPA_OTEL").
        """

        def _is_truthy(key: str) -> bool:
            return os.environ.get(key, "").lower() in ("1", "true", "yes")

        return cls(
            enabled=_is_truthy(f"{prefix}_ENABLED"),
            endpoint=os.environ.get(f"{prefix}_ENDPOINT", cls.endpoint),
            service_name=os.environ.get("OTEL_SERVICE_NAME", cls.service_name),
            console=_is_truthy(f"{prefix}_CONSOLE"),
        )
