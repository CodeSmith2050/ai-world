"""任务创建接口的单元测试。

使用 TestClient 模拟 HTTP 请求，验证任务创建流程的正确性。
Celery 任务使用 mock 避免连接 Redis。
"""

import io
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app


@pytest.fixture(scope="function")
def test_client(tmp_path, monkeypatch):
    """创建测试用客户端，使用临时数据库和临时上传目录。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 的 monkeypatch fixture。

    Yields:
        TestClient: FastAPI 测试客户端。
    """
    # 使用内存数据库，每个测试函数独立
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

    # 覆盖数据库依赖
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 覆盖上传目录为临时目录
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("main.UPLOAD_DIR", test_upload_dir)

    with TestClient(app) as client:
        yield client

    # 清理
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


class TestHealthCheck:
    """健康检查接口测试。"""

    def test_health_check_returns_ok(self, test_client):
        """测试健康检查接口返回正确状态。"""
        response = test_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestCreateTask:
    """任务创建接口测试。"""

    @patch("main.process_task")
    def test_create_task_success(self, mock_process_task, test_client, tmp_path):
        """测试正常创建任务。

        验证：
        1. 返回状态码 201
        2. 返回 task_id 和 status
        3. 图片文件已保存
        """
        # 准备测试图片
        image_content = b"fake image content"
        image_file = io.BytesIO(image_content)

        response = test_client.post(
            "/api/tasks",
            files={"image": ("test.png", image_file, "image/png")},
            data={"text": "这是一个测试任务"},
        )

        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "queued"
        assert len(data["task_id"]) > 0

        # 验证图片文件已保存
        upload_dir = tmp_path / "uploads"
        saved_files = list(upload_dir.glob("*.png"))
        assert len(saved_files) == 1
        assert saved_files[0].read_bytes() == image_content

        # 验证 Celery 任务被调用
        mock_process_task.delay.assert_called_once()

    @patch("main.process_task")
    def test_create_task_invalid_extension(self, mock_process_task, test_client):
        """测试上传不支持的文件扩展名。

        验证：返回状态码 400
        """
        image_file = io.BytesIO(b"fake content")

        response = test_client.post(
            "/api/tasks",
            files={"image": ("test.txt", image_file, "text/plain")},
            data={"text": "测试文本"},
        )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
        mock_process_task.delay.assert_not_called()

    @patch("main.process_task")
    def test_create_task_missing_text(self, mock_process_task, test_client):
        """测试缺少文本字段。

        验证：返回状态码 422（字段校验失败）
        """
        image_file = io.BytesIO(b"fake content")

        response = test_client.post(
            "/api/tasks",
            files={"image": ("test.png", image_file, "image/png")},
        )

        assert response.status_code == 422

    @patch("main.process_task")
    def test_create_task_missing_image(self, mock_process_task, test_client):
        """测试缺少图片字段。

        验证：返回状态码 422（字段校验失败）
        """
        response = test_client.post(
            "/api/tasks",
            data={"text": "测试文本"},
        )

        assert response.status_code == 422

    @patch("main.process_task")
    def test_create_task_database_record(self, mock_process_task, test_client):
        """测试创建任务后数据库记录正确。

        验证数据库中存在对应记录，字段值正确。
        """
        image_file = io.BytesIO(b"fake image content")

        response = test_client.post(
            "/api/tasks",
            files={"image": ("test.jpg", image_file, "image/jpeg")},
            data={"text": "数据库验证测试"},
        )

        task_id = response.json()["task_id"]

        # 通过覆盖后的数据库会话验证记录
        from database import get_db
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)

        from models import Task
        task = db.query(Task).filter(Task.id == task_id).first()
        assert task is not None
        assert task.status == "queued"
        assert task.progress == 0
        assert task.input_text == "数据库验证测试"
        assert task_id in task.input_image_path
        assert task.input_image_path.endswith(".jpg")
        assert task.output_file_path is None
        assert task.error_message is None

        db.close()
