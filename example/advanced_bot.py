"""
高级 KOOK Webhook Bot 示例（简化版社区助手）

演示点：
1. 事件优先级（高优先级预处理 + 普通业务处理）
2. 消息过滤（频道类型 / 消息类型 / 指定用户）
3. 正则命令匹配（/todo.add /todo.done /todo.list）
4. 系统事件处理（加入服务器）
5. 统一错误处理与 post 钩子统计

说明：
- 本示例强调“功能演示”，逻辑保持简单。
- 若未配置 bot_token，示例会仅记录日志，不主动调用 KOOK 发送接口。
"""

import os
from dataclasses import dataclass, field

from kook_webhook import APIError, Config, EventPriority, MessageType, WebhookApp


def _split_csv_env(name: str) -> list[str]:
    """读取逗号分隔环境变量并清理空值。"""
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class BotContext:
    """自定义应用上下文（可通过 ctx.data 访问）。"""

    admin_user_ids: set[str] = field(default_factory=set)
    focus_guild_ids: set[str] = field(default_factory=set)
    todos_by_channel: dict[str, list[str]] = field(default_factory=dict)
    processed_events: int = 0


def create_context(_app: WebhookApp) -> BotContext:
    return BotContext(
        admin_user_ids=set(_split_csv_env("DEMO_ADMIN_USER_IDS")),
        focus_guild_ids=set(_split_csv_env("DEMO_FOCUS_GUILD_IDS")),
    )


config = Config(
    host="0.0.0.0",
    port=8000,
    verify_token="xxx",  # 从 KOOK 开发者后台获取
    encrypt_key="yyy",  # 如果启用了消息加密
    bot_token=os.getenv("KOOK_WEBHOOK_BOT_TOKEN", ""),  # 可留空，仅做 webhook 演示
)
app = WebhookApp(config=config, context_factory=create_context)


async def safe_reply_channel(
    ctx, target_id: str, content: str, *, quote: str | None = None
) -> None:
    """安全发送频道消息：未配置 token 时仅打印日志。"""
    if not ctx.config.bot_token:
        ctx.logger.info(f"[dry-run] send_message target={target_id}, content={content}")
        return

    await ctx.bot.send_message(target_id=target_id, content=content, type=9, quote=quote)


@app.events.on_raw(priority=EventPriority.HIGHEST, stage="guard")
async def guard_raw_event(ctx, raw_data):
    """高优先级原始事件拦截：过滤机器人自身消息，避免回声循环。"""
    payload = raw_data.get("d", {}) if isinstance(raw_data, dict) else {}
    if payload.get("author_id") and payload.get("author_id") == ctx.config.bot_user_id:
        ctx.logger.debug("忽略机器人自身消息")
        return False
    return True


@app.events.on_message(
    priority=EventPriority.HIGH,
    channel_types=["GROUP"],
    message_types=[MessageType.TEXT, MessageType.KMARKDOWN],
    stage="audit",
)
async def audit_group_message(ctx, event, extra, content):
    """群消息审计：记录关键元信息。"""
    ctx.logger.info(
        "group message | guild=%s channel=%s user=%s content=%s",
        extra.guild_id,
        event.target_id,
        extra.author.username,
        content,
    )


@app.events.on_message(channel_types=["PERSON"], stage="dm")
async def handle_private_message(ctx, event, extra, content):
    """私聊入口：演示按频道类型过滤。"""
    if extra.author.bot:
        return
    await safe_reply_channel(
        ctx,
        event.target_id,
        f"(私聊) 你好，{extra.author.username}！你发送的是：{content}",
        quote=event.msg_id,
    )


@app.events.on_message(
    priority=EventPriority.HIGH,
    user_ids=_split_csv_env("DEMO_VIP_USER_IDS") or None,
    stage="vip",
)
async def handle_vip_user(ctx, event, extra, content):
    """指定用户消息处理：演示 user_ids 过滤。"""
    ctx.logger.info("VIP 用户消息：%s -> %s", extra.author.username, content)
    await safe_reply_channel(
        ctx,
        event.target_id,
        f"欢迎回来，{extra.author.nickname or extra.author.username}！",
        quote=event.msg_id,
    )


@app.events.on_command("help", description="查看命令帮助")
async def help_command(ctx, event, _extra, _command, _args):
    commands = ctx.app.events.list_commands()
    lines = ["可用命令："]
    for item in commands:
        desc = item.get("description") or "无描述"
        lines.append(f"- /{item['name']}: {desc}")
    await safe_reply_channel(ctx, event.target_id, "\n".join(lines), quote=event.msg_id)


@app.events.on_command(
    "regex:todo(?:\\.(?:add|done|list))?",
    description="Todo 示例：/todo.add /todo.done /todo.list",
)
async def todo_command(ctx, event, extra, command, args):
    """正则命令处理：按频道维护简易待办列表。"""
    channel_todos = ctx.data.todos_by_channel.setdefault(event.target_id, [])
    cmd = command.lower()

    if cmd in {"todo", "todo.list"}:
        if not channel_todos:
            await safe_reply_channel(ctx, event.target_id, "当前没有待办项。", quote=event.msg_id)
            return
        body = "\n".join(f"{idx}. {item}" for idx, item in enumerate(channel_todos, start=1))
        await safe_reply_channel(ctx, event.target_id, f"当前待办：\n{body}", quote=event.msg_id)
        return

    if cmd == "todo.add":
        task = args.strip()
        if not task:
            await safe_reply_channel(
                ctx, event.target_id, "用法：/todo.add <待办内容>", quote=event.msg_id
            )
            return
        channel_todos.append(task)
        await safe_reply_channel(
            ctx,
            event.target_id,
            f"已添加待办 #{len(channel_todos)}：{task}",
            quote=event.msg_id,
        )
        return

    if cmd == "todo.done":
        value = args.strip()
        if not value.isdigit():
            await safe_reply_channel(
                ctx, event.target_id, "用法：/todo.done <序号>", quote=event.msg_id
            )
            return
        index = int(value)
        if index <= 0 or index > len(channel_todos):
            await safe_reply_channel(
                ctx,
                event.target_id,
                f"序号无效，请输入 1 ~ {len(channel_todos)}",
                quote=event.msg_id,
            )
            return
        removed = channel_todos.pop(index - 1)
        await safe_reply_channel(
            ctx,
            event.target_id,
            f"已完成待办 #{index}：{removed}",
            quote=event.msg_id,
        )
        return

    await safe_reply_channel(ctx, event.target_id, "未识别的 todo 子命令。", quote=event.msg_id)


@app.events.on_command("announce", description="管理员广播：/announce <内容>")
async def announce_command(ctx, event, extra, _command, args):
    """管理员命令：演示业务权限判断。"""
    if ctx.data.admin_user_ids and extra.author.id not in ctx.data.admin_user_ids:
        await safe_reply_channel(ctx, event.target_id, "你没有权限执行该命令。", quote=event.msg_id)
        return

    text = args.strip()
    if not text:
        await safe_reply_channel(ctx, event.target_id, "用法：/announce <内容>", quote=event.msg_id)
        return

    await safe_reply_channel(ctx, event.target_id, f"📢 公告：{text}", quote=event.msg_id)


@app.events.on_system("joined_guild", description="机器人加入新服务器")
async def on_joined_guild(ctx, event, extra):
    """系统事件：加入服务器。"""
    guild_id = str(extra.body.get("guild_id", "unknown"))
    ctx.logger.info("收到 joined_guild 事件: guild_id=%s", guild_id)

    if ctx.data.focus_guild_ids and guild_id not in ctx.data.focus_guild_ids:
        ctx.logger.info("非关注服务器，跳过初始化逻辑")
        return

    # 演示：仅打印日志，实际项目可在这里做频道缓存、权限同步等初始化动作。
    ctx.logger.info("已完成服务器初始化流程（演示）")


@app.events.on_error()
async def global_error_handler(ctx, error, _handler, handler_type, context):
    """统一错误处理，避免单个处理器异常影响整体。"""
    ctx.logger.error("处理器异常 [%s]: %s | context=%s", handler_type, error, context)
    if isinstance(error, APIError):
        ctx.logger.error("KOOK APIError: code=%s message=%s", error.code, error.message)


@app.events.on_post(priority=EventPriority.LOWEST, stage="metrics")
async def post_event_metrics(ctx, _event):
    """事件后置统计。"""
    ctx.data.processed_events += 1
    if ctx.data.processed_events % 20 == 0:
        ctx.logger.info("累计处理事件数: %s", ctx.data.processed_events)


def main():
    app.run()


if __name__ == "__main__":
    main()
