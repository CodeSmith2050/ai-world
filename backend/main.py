"""FastAPI 应用入口模块。

提供健康检查等基础 API 端点，以及应用启动时的数据库初始化。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from schemas import HealthResponse


def init_db() -> None:
    """初始化数据库表结构。

    在应用启动时调用，创建所有尚未存在的数据库表。
    """
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。

    启动时初始化数据库，关闭时执行清理操作。

    Args:
        app: FastAPI 应用实例。
    """
    # 启动时执行
    init_db()
    yield
    # 关闭时执行（目前无需特殊操作）


# 创建 FastAPI 应用实例
app = FastAPI(
    title="AI World Technical Service API",
    description="从图片+文本到 3D 模型生成与仿真计算的技术服务 API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/api/health", response_model=HealthResponse, tags=["系统"])
def health_check() -> HealthResponse:
    """健康检查端点。

    用于验证服务是否正常运行。

    Returns:
        HealthResponse: 包含 status 字段的健康状态响应。
    """
    return HealthResponse(status="ok")
