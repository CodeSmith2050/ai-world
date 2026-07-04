"""异步任务定义模块。

包含任务处理的核心逻辑：解析需求、生成3D模型、执行仿真计算。
"""

import time
import zipfile
from pathlib import Path
from datetime import datetime, timezone

from celery_app import celery_app
from database import SessionLocal, BASE_DIR
from models import Task

# 结果文件存储目录
RESULTS_DIR = BASE_DIR / "media" / "results"


def _update_task(task_id: str, **kwargs) -> None:
    """更新任务字段的辅助函数。

    Args:
        task_id: 任务 ID。
        **kwargs: 需要更新的字段键值对。
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            for key, value in kwargs.items():
                setattr(task, key, value)
            task.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


@celery_app.task(name="process_task", bind=True)
def process_task(self, task_id: str, simulate_failure: bool = False) -> str:
    """处理任务的核心异步函数。

    包含模拟的处理步骤：解析需求、生成3D模型、执行仿真计算。
    每一步更新任务状态和进度，异常时标记为失败。

    Args:
        self: Celery 任务实例（bind=True）。
        task_id: 要处理的任务 ID。
        simulate_failure: 是否模拟失败，为 True 时抛出异常。

    Returns:
        str: 任务 ID。

    Raises:
        Exception: 当 simulate_failure 为 True 或处理过程中出错时。
    """
    # 创建结果目录
    result_dir = RESULTS_DIR / task_id
    result_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 步骤1：解析需求
        _update_task(
            task_id,
            status="processing",
            progress=10,
            current_step="解析需求...",
        )
        time.sleep(2)

        # 如果模拟失败，在此抛出异常
        if simulate_failure:
            raise RuntimeError("Simulated failure for testing")

        # 步骤2：生成3D模型
        _update_task(
            task_id,
            progress=40,
            current_step="生成3D模型...",
        )
        time.sleep(5)

        # 创建假的 STL 文件
        stl_path = result_dir / "model.stl"
        stl_path.write_text(
            "solid model\n"
            "  facet normal 0 0 1\n"
            "    outer loop\n"
            "      vertex 0 0 0\n"
            "      vertex 1 0 0\n"
            "      vertex 0 1 0\n"
            "    endloop\n"
            "  endfacet\n"
            "endsolid model\n"
        )

        # 步骤3：执行仿真计算
        _update_task(
            task_id,
            progress=70,
            current_step="执行仿真计算...",
        )
        time.sleep(10)

        # 创建假的 result.zip 文件
        zip_path = result_dir / "result.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(stl_path, "model.stl")
            zf.writestr(
                "report.txt",
                "Simulation Report\n"
                "=================\n"
                f"Task ID: {task_id}\n"
                f"Generated at: {datetime.now(timezone.utc).isoformat()}\n"
                "Result: All simulations passed.\n",
            )

        # 步骤4：完成
        _update_task(
            task_id,
            status="completed",
            progress=100,
            current_step="完成",
            output_file_path=str(zip_path),
        )

        return task_id

    except Exception as exc:
        # 异常处理：标记任务为失败
        _update_task(
            task_id,
            status="failed",
            current_step="失败",
            error_message=str(exc),
        )
        raise
