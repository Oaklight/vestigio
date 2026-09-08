# Vestigio

[English Version](README_en.md) | 中文版

轻量 OTEL 封装，用于 Agent/LLM 可观测性。

源自拉丁语 *vestigium*——"踪迹、足迹"。Vestigio 使用 [OpenInference](https://arize-ai.github.io/openinference/spec/) 和 [OTel GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) 语义约定，提供面向 Agent 的原生插桩。

## 特性

- **三种 Span 类型**：`agent_span()`、`llm_span()`、`tool_span()` —— 带有语义属性的上下文管理器
- **双重约定**：同时设置 OpenInference 和 OTel GenAI 属性，最大化后端兼容性
- **错误记录**：`set_span_error()` / `set_span_ok()` 实现状态映射和异常追踪
- **会话追踪**：agent span 支持 `session_id`、`user_id` 和任意 `metadata`
- **禁用时零开销**：未安装 OTEL SDK 或关闭遥测时使用 No-op 桩
- **无必要依赖**：OTEL 为可选项（`pip install vestigio[otel]`）

## 安装

```bash
pip install vestigio           # 仅核心，span 为静默桩
pip install vestigio[otel]     # + OTEL SDK，启用真实追踪
pip install vestigio[otlp]     # + OTLP 导出器，发送至 Jaeger、Tempo 等
```

## 快速开始

```python
from vestigio import (
    init_telemetry,
    agent_span,
    llm_span,
    tool_span,
    set_span_error,
    set_span_ok,
)
from vestigio._spans import set_llm_usage, set_agent_output

tracer = init_telemetry()

with agent_span(
    tracer,
    task="今天天气怎么样?",
    model="gpt-4",
    session_id="sess-001",
    user_id="user-42",
    metadata={"source": "cli"},
) as root:
    with llm_span(tracer, model="gpt-4", provider="openai") as llm:
        response = call_llm(...)
        set_llm_usage(llm, {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

    with tool_span(tracer, tool_name="get_weather") as tool:
        try:
            result = call_tool(...)
            set_span_ok(tool)
        except Exception as e:
            set_span_error(tool, e)

    set_agent_output(root, "今天天气晴朗。")
    set_span_ok(root)
```

## 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `VESTIGIO_ENABLED` | `false` | 总开关（`1`、`true`、`yes`） |
| `VESTIGIO_ENDPOINT` | `http://localhost:4317` | OTLP 端点 |
| `VESTIGIO_CONSOLE` | `false` | 开发用控制台导出器 |
| `OTEL_SERVICE_NAME` | `vestigio` | 标准 OTEL 服务名 |

消费方可使用自定义环境变量前缀：

```python
from vestigio import VestigioConfig, init_telemetry

config = VestigioConfig.from_env(prefix="TALPA_OTEL")
tracer = init_telemetry(config=config)
```

## 兼容后端

任何兼容 OTLP 的后端：Jaeger、Grafana Tempo、Arize Phoenix、Honeycomb、Datadog 等。

## 许可证

MIT
