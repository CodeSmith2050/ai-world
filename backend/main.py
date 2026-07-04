"""FastAPI 应用入口模块。

提供健康检查、任务创建、任务状态查询、结果下载等 API 端点，
以及应用启动时的数据库初始化。
"""

import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import Base, engine, get_db, BASE_DIR
from models import Task
from schemas import HealthResponse, TaskCreateResponse, TaskStatusResponse
from tasks import process_task

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
    simulate_failure: str = Form("false", description="是否模拟失败"),
    db: Session = Depends(get_db),
) -> TaskCreateResponse:
    """创建任务端点。

    接收图片和文本，保存图片到 media/uploads/，写入数据库，
    触发 Celery 异步任务处理，返回任务 ID 和初始状态。

    Args:
        image: 上传的图片文件。
        text: 输入的文本描述。
        simulate_failure: 是否模拟失败（"true" 时触发失败）。
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

    # 触发 Celery 异步任务
    should_simulate_failure = simulate_failure.lower() == "true"
    process_task.delay(task.id, should_simulate_failure)

    return TaskCreateResponse(task_id=task.id, status=task.status)


@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskStatusResponse,
    tags=["任务"],
)
def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
) -> TaskStatusResponse:
    """查询任务状态端点。

    根据任务 ID 返回当前状态、进度等信息。

    Args:
        task_id: 任务 ID。
        db: 数据库会话。

    Returns:
        TaskStatusResponse: 任务状态信息。

    Raises:
        HTTPException: 当任务不存在时返回 404。
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse.model_validate(task)


@app.get(
    "/api/tasks/{task_id}/download",
    tags=["任务"],
)
def download_task_result(
    task_id: str,
    db: Session = Depends(get_db),
) -> FileResponse:
    """下载任务结果文件端点。

    读取任务记录的 output_file_path，以文件流返回。
    仅当任务状态为 completed 且文件存在时可下载。

    Args:
        task_id: 任务 ID。
        db: 数据库会话。

    Returns:
        FileResponse: 结果文件流。

    Raises:
        HTTPException: 当任务不存在（404）、任务未完成（400）、
                       或文件不存在（404）时抛出。
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # 检查任务是否已完成
    if task.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not completed. Current status: {task.status}",
        )

    # 检查输出文件路径是否存在
    if not task.output_file_path:
        raise HTTPException(
            status_code=404,
            detail="Output file path is not set",
        )

    # 检查文件是否存在
    file_path = Path(task.output_file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Result file not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/zip",
        filename=f"{task_id}_result.zip",
    )
