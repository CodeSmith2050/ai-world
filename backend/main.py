"""FastAPI 应用入口模块。

提供健康检查、任务创建等 API 端点，以及应用启动时的数据库初始化。
"""

import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from database import Base, engine, get_db, BASE_DIR
from models import Task
from schemas import HealthResponse, TaskCreateResponse

# 上传文件存储目录
UPLOAD_DIR = BASE_DIR / "media" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片扩展名
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def init_db() -> None:
    """初始化数据库表结构。

    在应用启动时调用，创建所有尚未存在的数据库表。
    """
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。

    启动时初始化数据库和存储目录，关闭时执行清理操作。

    Args:
        app: FastAPI 应用实例。
    """
    # 启动时执行
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
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


@app.post(
    "/api/tasks",
    response_model=TaskCreateResponse,
    status_code=201,
    tags=["任务"],
)
async def create_task(
    image: UploadFile = File(..., description="上传的图片文件"),
    text: str = Form(..., description="输入文本描述"),
    db: Session = Depends(get_db),
) -> TaskCreateResponse:
    """创建任务端点。

    接收图片和文本，保存图片到 media/uploads/，写入数据库，
    返回任务 ID 和初始状态。

    Args:
        image: 上传的图片文件。
        text: 输入的文本描述。
        db: 数据库会话。

    Returns:
        TaskCreateResponse: 包含 task_id 和 status 的响应。

    Raises:
        HTTPException: 当文件扩展名不支持时返回 400。
    """
    # 校验文件扩展名
    file_ext = Path(image.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension {file_ext} is not allowed. "
            f"Allowed: {ALLOWED_EXTENSIONS}",
        )

    # 创建数据库记录，先获取 task_id 用于文件命名
    task = Task(
        input_text=text,
        input_image_path="",  # 占位，后面更新
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 使用 task_id 作为文件名，避免冲突
    saved_filename = f"{task.id}{file_ext}"
    saved_path = UPLOAD_DIR / saved_filename

    # 保存上传的图片文件
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # 更新数据库中的图片路径
    task.input_image_path = str(saved_path)
    db.commit()
    db.refresh(task)

    return TaskCreateResponse(task_id=task.id, status=task.status)
