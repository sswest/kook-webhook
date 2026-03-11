# KOOK Webhook 示例

本目录包含使用 `kook-webhook` SDK 的示例代码。

## 示例列表

### 1. simple_bot.py
最简单的机器人示例，展示基本用法:
- 创建 WebhookApp
- 注册命令处理器
- 注册消息处理器

### 2. advanced_bot.py
高级功能示例:
- 事件优先级
- 消息过滤（按服务器/用户/频道类型）
- 正则表达式命令匹配
- 错误处理
- 系统事件处理

## 运行示例

```bash
# 简单机器人
python example/simple_bot.py

# 高级机器人
python example/advanced_bot.py
```

## 配置说明

在运行示例前，请确保修改以下配置:
- `verify_token`: 从 KOOK 开发者后台获取
- `encrypt_key`: 如果启用了消息加密

## 开发 KOOK 机器人

1. 访问 [KOOK 开发者平台](https://developer.kookapp.cn/)
2. 创建机器人应用
3. 配置 Webhook 回调地址
4. 获取 verify_token 和 encrypt_key
5. 修改示例代码中的配置
6. 启动机器人
