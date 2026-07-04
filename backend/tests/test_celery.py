"""Celery 异步任务的单元测试。

直接调用 process_task 函数（同步模式），验证状态流转和文件生成。
"""

import io
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, SessionLocal
from models import Task
import tasks as tasks_module


@pytest.fixture(scope="function")
def test_db(tmp_path, monkeypatch):
    """创建测试用数据库和环境。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 的 monkeypatch fixture。

    Yields:
        tuple: (TestingSessionLocal, test_results_dir)
    """
    # 使用临时数据库
    test_db_url = f"sqlite:///{tmp_path / 'test.db'}"
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    # 创建表
    Base.metadata.create_all(bind=test_engine)

    # 覆盖 tasks 模块中的 SessionLocal
    monkeypatch.setattr("tasks.SessionLocal", TestingSessionLocal)

    # 覆盖结果目录
    test_results_dir = tmp_path / "results"
    test_results_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("tasks.RESULTS_DIR", test_results_dir)

    yield TestingSessionLocal, test_results_dir

    # 清理
    Base.metadata.drop_all(bind=test_engine)


def create_test_task(db_session, text="测试任务"):
    """创建测试用任务记录。

    Args:
        db_session: 数据库会话。
        text: 任务文本。

    Returns:
        Task: 创建的任务对象。
    """
    task = Task(
        input_text=text,
        input_image_path="/fake/path/image.png",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


class TestProcessTaskSuccess:
    """任务正常处理流程测试。"""

    def test_process_task_success(self, test_db):
        """测试任务正常处理流程。

        验证：
        1. 任务最终状态为 completed
        2. 进度为 100
        3. 生成了 STL 文件和 ZIP 文件
        4. output_file_path 已设置
        """
        TestingSessionLocal, test_results_dir = test_db

        # 创建测试任务
        db = TestingSessionLocal()
        task = create_test_task(db, "正常处理测试")
        task_id = task.id
        db.close()

        # 直接调用任务函数（同步执行）
        tasks_module.process_task.run(task_id, simulate_failure=False)

        # 验证最终状态
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == task_id).first()
        assert task.status == "completed"
        assert task.progress == 100
        assert task.output_file_path is not None
        assert task.output_file_path.endswith("result.zip")
        assert task.error_message is None
        db.close()

        # 验证文件已生成
        result_dir = test_results_dir / task_id
        assert (result_dir / "model.stl").exists()
        assert (result_dir / "result.zip").exists()

        # 验证 ZIP 文件内容
        with zipfile.ZipFile(result_dir / "result.zip", "r") as zf:
            assert "model.stl" in zf.namelist()
            assert "report.txt" in zf.namelist()


class TestProcessTaskFailure:
    """任务失败处理流程测试。"""

    def test_process_task_simulate_failure(self, test_db):
        """测试任务模拟失败流程。

        验证：
        1. 任务最终状态为 failed
        2. error_message 包含错误信息
        3. output_file_path 为 None
        """
        TestingSessionLocal, test_results_dir = test_db

        # 创建测试任务
        db = TestingSessionLocal()
        task = create_test_task(db, "失败测试")
        task_id = task.id
        db.close()

        # 调用任务函数，模拟失败
        try:
            tasks_module.process_task.run(task_id, simulate_failure=True)
        except RuntimeError:
            pass  # 预期会抛出异常

        # 验证最终状态
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == task_id).first()
        assert task.status == "failed"
        assert task.error_message is not None
        assert "Simulated failure" in task.error_message
        assert task.output_file_path is None
        db.close()


class TestGetTaskStatus:
    """任务状态查询测试。"""

    def test_get_nonexistent_task(self, test_db):
        """测试查询不存在的任务。

        验证：数据库中找不到记录
        """
        TestingSessionLocal, _ = test_db
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == "non-existent").first()
        assert task is None
        db.close()

    def test_task_status_transitions(self, test_db):
        """测试任务状态转换。

        验证：任务从 queued 转换到 completed
        """
        TestingSessionLocal, _ = test_db

        # 创建任务，初始状态为 queued
        db = TestingSessionLocal()
        task = create_test_task(db, "状态转换测试")
        assert task.status == "queued"
        assert task.progress == 0
        task_id = task.id
        db.close()

        # 执行任务
        tasks_module.process_task.run(task_id, simulate_failure=False)

        # 验证最终状态
        db = TestingSessionLocal()
        task = db.query(Task).filter(Task.id == task_id).first()
        assert task.status == "completed"
        assert task.progress == 100
        db.close()
