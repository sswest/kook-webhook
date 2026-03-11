# KOOK Webhook SDK

Python SDK for receiving, validating, and handling KOOK Webhook events, with an optional KOOK OpenAPI client.

Language:
- English (default): this section
- 中文文档: see [README.zh-CN.md](README.zh-CN.md)

## Features

- Async webhook server powered by `Sanic`
- Strongly typed models and config with `Pydantic`
- Event system with rich handler types (`on_message`, `on_command`, `on_system`, etc.)
- Built-in decryption (`AES-256-CBC`) and optional auto zlib decompression
- Context-first handler design to share app resources cleanly
- Optional KOOK REST API client via `KookClient`

## Installation

### From source (current repository)

```bash
pip install -e .
```

### Install dev dependencies

```bash
pip install -e ".[dev]"
```

## Quick Start

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
    ctx.logger.info("Received /hello command")

app.run()
```

## Handler Types

| Decorator | Signature | Purpose |
| --- | --- | --- |
| `on_raw` | `async def(ctx, raw_data)` | Run before payload parsing |
| `on_message` | `async def(ctx, event, extra, content)` | Process user messages |
| `on_command` | `async def(ctx, event, extra, command, args)` | Process slash-like commands |
| `on_system` | `async def(ctx, event, extra)` | Handle system events |
| `on_post` | `async def(ctx, event)` | Run after all handlers |
| `on_error` | `async def(ctx, error, handler, handler_type, context)` | Global error fallback |

All handlers receive `ctx` as the first argument.

## Context Usage

`ctx` provides access to common app resources:

```python
@app.events.on_message()
async def handle_message(ctx, event, extra, content):
    ctx.logger.info("message received")
    _host = ctx.config.host
    _app = ctx.app
```

You can attach custom resources to `app` and access them from `ctx` in handlers.

## Configuration

You can configure with constructor parameters or environment variables.

Common variables:
- `KOOK_WEBHOOK_HOST`
- `KOOK_WEBHOOK_PORT`
- `KOOK_WEBHOOK_VERIFY_TOKEN`
- `KOOK_WEBHOOK_ENCRYPT_KEY`
- `KOOK_WEBHOOK_AUTO_COMPRESS`
- `KOOK_WEBHOOK_LOG_LEVEL`

Boolean env values support `true/false`, `1/0`, `yes/no`, `on/off` (case-insensitive).

## Optional OpenAPI Client

The package also exports `KookClient` for KOOK REST API operations.

```python
from kook_webhook import KookClient

client = KookClient(token="your_bot_token")
# call API methods from the SDK client
```

## Project Layout

```text
kook_webhook/
├── kook_webhook/      # package source
├── example/           # runnable examples
├── tests/             # test suite
├── pyproject.toml
├── pytest.ini
└── README.md
```

## Development

Run tests:

```bash
pytest
```

Examples:
- `example/simple_bot.py`: minimal bot
- `example/advanced_bot.py`: advanced handlers and routing
- `example/sdk_example.py`: OpenAPI client examples

## References

- [KOOK Webhook Documentation](https://developer.kookapp.cn/doc/webhook)
- [KOOK Event Documentation](https://developer.kookapp.cn/doc/event/event-introduction)
- [KOOK Object Documentation](https://developer.kookapp.cn/doc/objects)

## License

MIT
