"""Celery 应用配置模块。

配置 Celery 使用 Redis 作为消息代理，用于异步任务处理。
测试环境下可使用内存 broker 避免外部依赖。
"""

import os
from celery import Celery

# Redis broker URL，默认使用本地 Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# 测试模式下使用内存 broker
IS_TESTING = os.getenv("CELERY_TESTING", "false").lower() == "true"

if IS_TESTING:
    BROKER_URL = "memory://"
    BACKEND_URL = "cache+memory://"
else:
    BROKER_URL = REDIS_URL
    BACKEND_URL = REDIS_URL

# 创建 Celery 应用实例
celery_app = Celery(
    "ai_world",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

# 配置 Celery
celery_app.conf.update(
    # 任务序列化格式
    task_serializer="json",
    # 结果序列化格式
    result_serializer="json",
    # 接受的内容类型
    accept_content=["json"],
    # 时区
    timezone="UTC",
    # 启用任务结果
    task_track_started=True,
    # 任务超时时间（秒）
    task_time_limit=300,
    # 软超时时间（秒）
    task_soft_time_limit=240,
)


def get_celery_app() -> Celery:
    """获取 Celery 应用实例。

    Returns:
        Celery: 配置好的 Celery 应用实例。
    """
    return celery_app
