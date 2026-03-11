"""
简单的 KOOK Webhook Bot 示例

这个示例展示了如何使用 kook-webhook SDK 快速创建一个机器人
"""

from kook_webhook import Config, WebhookApp

# 创建配置
config = Config(
    host="0.0.0.0",
    port=8000,
    verify_token="xxx",  # 从 KOOK 开发者后台获取
    encrypt_key="yyy",  # 如果启用了消息加密
)

# 创建应用
app = WebhookApp(config)


# 注册命令处理器
@app.events.on_command("ping", description="测试机器人是否在线")
async def ping_handler(ctx, event, extra, command, args):
    ctx.logger.info("收到 ping 命令, 响应 pong!")
    # 可以通过 ctx 访问应用资源: ctx.app, ctx.config, ctx.logger


@app.events.on_command("hello", description="打招呼")
async def hello_handler(ctx, event, extra, command, args):
    ctx.logger.info(f"收到 hello 命令 from {extra.author.username}!")


# 注册消息处理器
@app.events.on_message(message_types=[1])  # 只处理文字消息
async def text_message_handler(ctx, event, extra, content):
    ctx.logger.info(f"收到文字消息: {content}")


def main():
    # 启动服务器
    app.run()


if __name__ == "__main__":
    main()
