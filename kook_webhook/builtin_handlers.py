"""
Builtin event handlers

For debugging and logging
"""

from typing import Any

from .event_manager import Context, EventPriority
from .models import MessageExtra, MessageType, SystemEventExtra, WebhookEvent


async def log_raw_event(ctx: Context, raw_data: dict[str, Any]):
    """Log all raw events"""
    webhook_data = raw_data.get("d", {})
    ctx.logger.debug(
        f"Raw event: msg_id={webhook_data.get('msg_id')}, "
        f"type={webhook_data.get('type')}, "
        f"channel_type={webhook_data.get('channel_type')}"
    )


async def log_message_summary(ctx: Context, event: WebhookEvent, extra: MessageExtra, content: str):
    """Log message summary"""
    ctx.logger.info(
        f"Message: id={event.msg_id}, "
        f"type={event.type}, "
        f"channel={extra.channel_name}, "
        f"author={extra.author.username}#{extra.author.identify_num}, "
        f"content={content[:50]}..."
    )


async def builtin_help_command(
    ctx: Context, event: WebhookEvent, extra: MessageExtra, command: str, args: str
):
    """Builtin help command"""
    commands = ctx.app.events.list_commands()
    ctx.logger.info(f"Available commands: {commands}")
    # Return False to block subsequent handlers
    return False


async def log_system_event(ctx: Context, event: WebhookEvent, extra: SystemEventExtra):
    """Log system events"""
    ctx.logger.info(f"System event: type={extra.type}, body={extra.body}")
