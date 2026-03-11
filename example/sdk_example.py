"""
KOOK SDK 示例代码

演示如何使用 KOOK API Client 进行各种操作
"""

import asyncio

from kook_webhook import (
    APIError,
    DirectMessageCreateRequest,
    KookClient,
    MessageCreateRequest,
    MessagePinRequest,
    MessageReactionRequest,
    UserChatCreateRequest,
)


async def basic_example():
    """基本使用示例"""
    # 使用 async context manager 自动管理连接
    async with KookClient(token="1/NDQ0MTc=/TIrztKrCw2yGfP/cIA1WsQ==") as client:
        guild_id = "3937561724737356"
        channel_id = "5878237129106449"
        user_id = "2860579476"

        # user_list = await client.guild_user_list(guild_id="3937561724737356", page_size=100)
        # for u in user_list.items:
        #     print(u)

        # user_list = await client.guild_user_list(
        #     guild_id=first_guild.id,
        #     page_size=20
        # )

        # 发送频道消息
        # response = await client.send_message(
        #     target_id=channel_id,
        #     content="院长来了，床位就有了！",
        #     type=9,  # KMarkdown 消息
        # )
        # print(f"消息已发送，ID: {response.msg_id}")

        # 获取频道消息列表
        # msg_list = await client.message_list(target_id=channel_id, page_size=20)
        # print(f"获取到 {len(msg_list.items)} 条消息")

        # # 消息已自动解析为 Pydantic 模型
        # if msg_list.items:
        #     for msg in msg_list.items:
        #         print(f"消息内容: {msg}")
        #     # first_msg = msg_list.items[0]
        #     # print(f"第一条消息内容: {first_msg.content}")
        #     # print(f"发送者: {first_msg.author.username}")

        # # 获取消息详情
        # if msg_list.items:
        #     msg_id = msg_list.items[-1].id
        #     detail = await client.message_view(msg_id=msg_id)
        #     print(f"消息详情: {detail}")

        # # 发送私聊消息
        dm_response = await client.send_direct_message(
            target_id=user_id,
            content="这是一个私聊消息",
            type=9,
        )
        print(f"私聊消息已发送，ID: {dm_response.msg_id}")

        # # 添加表情回应
        # if msg_list.items:
        #     await client.message_add_reaction(
        #         MessageReactionRequest(msg_id=msg_id, emoji="👍")
        #     )


async def advanced_example():
    """高级功能示例"""
    async with KookClient(token="your_bot_token") as client:
        # 使用完整的 Pydantic 模型
        create_request = MessageCreateRequest(
            type=9,
            target_id="channel_id_123",
            content="使用完整模型发送的消息",
            nonce="custom_nonce_123",
            temp_target_id="user_id_456",  # 发送临时消息，只对指定用户可见
        )
        response = await client.message_create(create_request)
        print(f"消息 ID: {response.msg_id}")

        # 更新消息
        from kook_webhook import MessageUpdateRequest

        update_request = MessageUpdateRequest(
            msg_id=response.msg_id,
            content="更新后的消息内容",
        )
        await client.message_update(update_request)

        # 置顶消息
        pin_request = MessagePinRequest(
            msg_id=response.msg_id,
            target_id="channel_id_123",
        )
        await client.message_pin(pin_request)

        # 获取用户聊天列表
        chat_list = await client.user_chat_list(page=1, page_size=20)
        print(f"聊天会话数: {chat_list.meta.total}")

        # 创建私聊会话
        create_chat_request = UserChatCreateRequest(target_id="user_id_456")
        chat_info = await client.user_chat_create(create_chat_request)
        print(f"聊天 Code: {chat_info.code}")

        # 通过 Chat Code 发送私聊消息
        dm_request = DirectMessageCreateRequest(
            chat_code=chat_info.code,
            content="通过 Chat Code 发送的私聊消息",
            type=9,
        )
        dm_response = await client.direct_message_create(dm_request)
        print(f"私聊消息 ID: {dm_response.msg_id}")

        # 获取私聊消息列表
        dm_messages = await client.direct_message_list(chat_code=chat_info.code, page_size=20)
        print(f"私聊消息数: {len(dm_messages.items)}")

        # 获取消息的表情回应
        if dm_messages.items:
            reaction_users = await client.direct_message_reaction_list(
                msg_id=dm_messages.items[0].id, emoji="👍"
            )
            print(f"有 {len(reaction_users)} 人回应了此消息")
            for user in reaction_users:
                print(f"  - {user.username} (时间: {user.reaction_time})")

        # 删除消息
        from kook_webhook import MessageDeleteRequest

        delete_request = MessageDeleteRequest(msg_id=response.msg_id)
        await client.message_delete(delete_request)


async def webhook_with_client_example():
    """结合 Webhook 和 Client 的示例"""
    from kook_webhook import Config, WebhookApp

    # 创建配置
    config = Config(
        host="0.0.0.0",
        port=8000,
        verify_token="your_verify_token",
        encrypt_key="your_encrypt_key",
    )

    # 创建应用和客户端
    app = WebhookApp(config)
    client = KookClient(token="your_bot_token")

    # 将客户端附加到 app，以便在处理器中访问
    app.client = client

    # 注册命令处理器
    @app.events.on_command("hello")
    async def hello_handler(ctx, event, extra, command, args):
        # 使用 client 发送回复
        await ctx.client.send_message(
            target_id=event.target_id,
            content=f"你好, {extra.author.nickname or extra.author.username}!",
        )
        ctx.logger.info(f"已向 {event.target_id} 发送回复")

    # 注册消息处理器
    @app.events.on_message()
    async def message_handler(ctx, event, extra, content):
        # 回复用户发送的消息（避免机器人循环）
        if not extra.author.bot:
            await ctx.client.send_message(
                target_id=event.target_id,
                content=f"你发送了: {content}",
                quote=event.msg_id,  # 回复原消息
            )

    # 启动服务器
    app.run()


async def discover_guilds_and_channels():
    """自动查找服务器和频道并打印相关信息"""
    async with KookClient(token="1/NDQ0MTc=/TIrztKrCw2yGfP/cIA1WsQ==") as client:
        # 获取机器人加入的所有服务器
        print("=" * 50)
        print("正在获取服务器列表...")
        print("=" * 50)

        guild_list = await client.guild_list(page_size=50)
        print(f"\n共找到 {guild_list.meta.total} 个服务器:\n")

        for i, guild in enumerate(guild_list.items, 1):
            print(f"{i}. 服务器名称: {guild.name}")
            print(f"   服务器 ID: {guild.id}")
            print(f"   主题: {guild.topic or '(无)'}")
            print(f"   默认频道 ID: {guild.default_channel_id}")
            print(f"   欢迎频道 ID: {guild.welcome_channel_id}")
            print(f"   等级: {guild.level}")
            print(f"   助力数: {guild.boost_num}")
            print()

        # 如果有服务器，获取第一个服务器的详细信息和频道列表
        if guild_list.items:
            first_guild = guild_list.items[0]
            print("=" * 50)
            print(f"正在获取服务器「{first_guild.name}」的详细信息...")
            print("=" * 50)

            guild_detail = await client.guild_view(guild_id=first_guild.id)

            print(f"\n服务器 ID: {guild_detail.id}")
            print(f"服务器名称: {guild_detail.name}")
            print(f"所有者 ID: {guild_detail.user_id}")
            print(f"通知类型: {guild_detail.notify_type}")
            print(f"区域: {guild_detail.region}")
            print(f"开放 ID: {guild_detail.open_id}")
            print(f"图标: {guild_detail.icon}")

            # 显示角色信息
            if guild_detail.roles:
                print(f"\n服务器角色 ({len(guild_detail.roles)} 个):")
                for role in guild_detail.roles:
                    print(
                        f"  - [{role.role_id}] {role.name} (颜色: {role.color}, 位置: {role.position})"
                    )

            # 获取频道列表
            print("\n" + "=" * 50)
            print(f"正在获取服务器「{first_guild.name}」的频道列表...")
            print("=" * 50)

            # 获取文本频道
            text_channels = await client.channel_list(
                guild_id=first_guild.id, type=1, page_size=50  # 1 = 文本频道
            )

            # 获取语音频道
            voice_channels = await client.channel_list(
                guild_id=first_guild.id, type=2, page_size=50  # 2 = 语音频道
            )

            print(f"\n文本频道 ({text_channels.meta.total} 个):")
            for channel in text_channels.items:
                channel_type_str = "📁 分组" if channel.is_category else "💬 文本"
                print(f"  {channel_type_str} [{channel.id}] {channel.name}")
                if not channel.is_category:
                    print(f"      主题: {channel.topic or '(无)'}")
                    print(f"      等级: {channel.level}, 慢速模式: {channel.slow_mode}秒")

            print(f"\n语音频道 ({voice_channels.meta.total} 个):")
            for channel in voice_channels.items:
                channel_type_str = "📁 分组" if channel.is_category else "🎙️ 语音"
                print(f"  {channel_type_str} [{channel.id}] {channel.name}")
                if not channel.is_category:
                    print(f"      主题: {channel.topic or '(无)'}")
                    print(
                        f"      人数限制: {channel.limit_amount}, 语音质量: {getattr(channel, 'voice_quality', 'default')}"
                    )

            # 获取第一个文本频道的详细信息
            if text_channels.items:
                first_text_channel = next(
                    (c for c in text_channels.items if not c.is_category), text_channels.items[0]
                )
                print("\n" + "=" * 50)
                print(f"正在获取频道「{first_text_channel.name}」的详细信息...")
                print("=" * 50)

                channel_detail = await client.channel_view(
                    target_id=first_text_channel.id, need_children=True
                )

                print(f"\n频道 ID: {channel_detail.id}")
                print(f"频道名称: {channel_detail.name}")
                print(f"频道类型: {channel_detail.type} (1=文本, 2=语音)")
                print(f"分组 ID: {channel_detail.parent_id}")
                print(f"主题: {channel_detail.topic or '(无)'}")
                print(f"等级: {channel_detail.level}")
                print(f"慢速模式: {channel_detail.slow_mode}秒")
                print(f"人数限制: {channel_detail.limit_amount}")
                print(f"是否有密码: {channel_detail.has_password}")
                print(f"权限同步: {channel_detail.permission_sync}")

                # 显示子频道
                if channel_detail.children:
                    print(f"\n子频道 ({len(channel_detail.children)} 个):")
                    for child_id in channel_detail.children:
                        print(f"  - {child_id}")

                # 显示权限覆盖
                if channel_detail.permission_overwrites:
                    print(f"\n角色权限覆盖 ({len(channel_detail.permission_overwrites)} 个):")
                    for perm in channel_detail.permission_overwrites:
                        print(f"  - 角色 [{perm.role_id}]: allow={perm.allow}, deny={perm.deny}")

                if channel_detail.permission_users:
                    print(f"\n用户权限覆盖 ({len(channel_detail.permission_users)} 个):")
                    for user_perm in channel_detail.permission_users:
                        user_info = user_perm.user
                        username = (
                            user_info.get("username", "unknown")
                            if isinstance(user_info, dict)
                            else "unknown"
                        )
                        print(
                            f"  - 用户 [{username}]: allow={user_perm.allow}, deny={user_perm.deny}"
                        )

            # 获取服务器用户列表
            print("\n" + "=" * 50)
            print(f"正在获取服务器「{first_guild.name}」的用户列表...")
            print("=" * 50)

            user_list = await client.guild_user_list(guild_id=first_guild.id, page_size=20)

            print(f"\n用户统计:")
            print(f"  总用户数: {user_list.user_count}")
            print(f"  在线用户: {user_list.online_count}")
            print(f"  离线用户: {user_list.offline_count}")

            print(f"\n前 {len(user_list.items)} 个用户:")
            for user in user_list.items:
                username = user.username
                nickname = user.nickname
                user_id = user.id
                online = user.online
                bot = user.bot

                display_name = f"{nickname} ({username})" if nickname else username
                status = "🤖 机器人" if bot else ("🟢 在线" if online else "⚪ 离线")
                print(f"  - [{user_id}] {display_name} {status}")


async def error_handling_example():
    """错误处理示例"""
    async with KookClient(token="your_bot_token") as client:
        try:
            # 尝试发送消息到不存在的频道
            response = await client.send_message(
                target_id="invalid_channel_id",
                content="Hello!",
            )
        except APIError as e:
            print(f"API 错误: [{e.code}] {e.message}")
            if e.code == 403:
                print("权限不足，请检查机器人权限")
            elif e.code == 404:
                print("频道或用户不存在")


if __name__ == "__main__":
    # 自动查找服务器和频道示例
    # print("=== 自动查找服务器和频道 ===")
    # asyncio.run(discover_guilds_and_channels())

    # 注意：如果要运行其他示例，需要配置正确的 token
    # print("\n=== 基本使用示例 ===")
    asyncio.run(basic_example())

    # print("\n=== 高级功能示例 ===")
    # asyncio.run(advanced_example())

    # print("\n=== 错误处理示例 ===")
    # asyncio.run(error_handling_example())

    # print("\n=== 结合 Webhook 和 Client 示例 ===")
    # asyncio.run(webhook_with_client_example())
