# KOOK Webhook SDK（中文）

用于接收、校验并处理 KOOK Webhook 事件的 Python SDK，包含可选的 KOOK OpenAPI 客户端能力。

Language:
- 中文（当前文档）
- English: see [README.md](README.md)

## 功能特性

- 基于 `Sanic` 的异步 Webhook 服务
- 使用 `Pydantic` 的强类型配置与数据模型
- 完整事件处理器体系（`on_message`、`on_command`、`on_system` 等）
- 内置 `AES-256-CBC` 解密与可选 zlib 自动解压
- 通过 `Context` 在处理器中访问应用资源
- 可选 `KookClient` 用于调用 KOOK OpenAPI

## 安装

### 从源码安装（当前仓库）

```bash
pip install -e .
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

## 快速开始

```python
from kook_webhook import Config, WebhookApp

config = Config(
    host="0.0.0.0",
    port=8000,
    verify_token="your_verify_token",
    encrypt_key="your_encrypt_key",
)

app = WebhookApp(config)

@app.events.on_command("hello")
async def hello_handler(ctx, event, extra, command, args):
    ctx.logger.info("收到 /hello 命令")

app.run()
```

## 处理器类型

| 装饰器 | 函数签名 | 用途 |
| --- | --- | --- |
| `on_raw` | `async def(ctx, raw_data)` | 在解析前处理原始请求体 |
| `on_message` | `async def(ctx, event, extra, content)` | 处理用户消息 |
| `on_command` | `async def(ctx, event, extra, command, args)` | 处理命令消息 |
| `on_system` | `async def(ctx, event, extra)` | 处理系统事件 |
| `on_post` | `async def(ctx, event)` | 所有处理器完成后执行 |
| `on_error` | `async def(ctx, error, handler, handler_type, context)` | 全局错误兜底 |

所有处理器第一个参数均为 `ctx`。

## Context 使用方式

`ctx` 提供对应用常用资源的访问：

```python
@app.events.on_message()
async def handle_message(ctx, event, extra, content):
    ctx.logger.info("message received")
    _host = ctx.config.host
    _app = ctx.app
```

你可以把自定义资源挂到 `app` 上，再在处理器里通过 `ctx` 访问。

## 配置

支持构造函数参数和环境变量两种配置方式。

常用环境变量：
- `KOOK_WEBHOOK_HOST`
- `KOOK_WEBHOOK_PORT`
- `KOOK_WEBHOOK_VERIFY_TOKEN`
- `KOOK_WEBHOOK_ENCRYPT_KEY`
- `KOOK_WEBHOOK_AUTO_COMPRESS`
- `KOOK_WEBHOOK_LOG_LEVEL`

布尔环境变量支持 `true/false`、`1/0`、`yes/no`、`on/off`（不区分大小写）。

## 可选 OpenAPI 客户端

包中导出了 `KookClient` 用于调用 KOOK REST API：

```python
from kook_webhook import KookClient

client = KookClient(token="your_bot_token")
# call API methods from the SDK client
```

## 项目结构

```text
kook_webhook/
├── kook_webhook/      # package source
├── example/           # runnable examples
├── tests/             # test suite
├── pyproject.toml
├── pytest.ini
├── README.md
└── README.zh-CN.md
```

## 开发

运行测试：

```bash
pytest
```

示例代码：
- `example/simple_bot.py`：最小示例
- `example/advanced_bot.py`：高级处理器与路由示例
- `example/sdk_example.py`：OpenAPI 客户端示例

## 参考文档

- [KOOK Webhook 文档](https://developer.kookapp.cn/doc/webhook)
- [KOOK 事件文档](https://developer.kookapp.cn/doc/event/event-introduction)
- [KOOK 对象文档](https://developer.kookapp.cn/doc/objects)

## 许可证

MIT
