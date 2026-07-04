"""结果下载接口的单元测试。

验证下载接口在各种场景下的行为：正常下载、任务未完成、任务不存在等。
"""

import io
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import Task
import tasks as tasks_module


@pytest.fixture(scope="function")
def test_client(tmp_path, monkeypatch):
    """创建测试用客户端，使用临时数据库和临时目录。

    Args:
        tmp_path: pytest 提供的临时目录。
        monkeypatch: pytest 的 monkeypatch fixture。

    Yields:
        TestClient: FastAPI 测试客户端。
    """
    test_db_url = f"sqlite:///{tmp_path / 'test.db'}"
    test_engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # 覆盖上传和结果目录
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("main.UPLOAD_DIR", test_upload_dir)

    test_results_dir = tmp_path / "results"
    test_results_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("tasks.RESULTS_DIR", test_results_dir)

    # 覆盖 tasks 的 SessionLocal
    monkeypatch.setattr("tasks.SessionLocal", TestingSessionLocal)

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


class TestDownloadEndpoint:
    """下载接口测试。"""

    def test_download_task_not_found(self, test_client):
        """测试下载不存在的任务。

        验证：返回状态码 404
        """
        response = test_client.get("/api/tasks/nonexistent/download")
        assert response.status_code == 404
        assert response.json()["detail"] == "Task not found"

    @patch("main.process_task")
    def test_download_task_not_completed(self, mock_process_task, test_client):
        """测试下载未完成的任务。

        验证：返回状态码 400
        """
        # 创建任务（mock 掉 Celery，任务不会执行）
        image_file = io.BytesIO(b"fake image")
        create_response = test_client.post(
            "/api/tasks",
            files={"image": ("test.png", image_file, "image/png")},
            data={"text": "测试"},
        )
        task_id = create_response.json()["task_id"]

        # 尝试下载（任务状态为 queued）
        response = test_client.get(f"/api/tasks/{task_id}/download")
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]

    def test_download_task_success(self, test_client, tmp_path):
        """测试正常下载已完成任务的结果。

        验证：
        1. 返回状态码 200
        2. 响应为文件流
        3. 文件内容为有效的 ZIP
        """
        # 直接在数据库中创建一个已完成的任务
        from database import get_db
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)

        # 创建结果文件
        result_dir = tmp_path / "results" / "test-task-id"
        result_dir.mkdir(parents=True, exist_ok=True)
        zip_path = result_dir / "result.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("model.stl", "fake STL content")
            zf.writestr("report.txt", "fake report")

        # 创建已完成的任务记录
        task = Task(
            id="test-task-id",
            status="completed",
            progress=100,
            input_text="测试下载",
            input_image_path="/fake/path/image.png",
            output_file_path=str(zip_path),
        )
        db.add(task)
        db.commit()
        db.close()

        # 下载文件
        response = test_client.get("/api/tasks/test-task-id/download")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

        # 验证下载的文件内容
        content = response.content
        download_path = tmp_path / "downloaded.zip"
        download_path.write_bytes(content)

        with zipfile.ZipFile(download_path, "r") as zf:
            assert "model.stl" in zf.namelist()
            assert "report.txt" in zf.namelist()

    def test_download_task_file_not_found(self, test_client, tmp_path):
        """测试下载已完成任务但文件不存在。

        验证：返回状态码 404
        """
        from database import get_db
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)

        # 创建已完成任务但 output_file_path 指向不存在的文件
        task = Task(
            id="missing-file-task",
            status="completed",
            progress=100,
            input_text="测试",
            input_image_path="/fake/path/image.png",
            output_file_path="/nonexistent/path/result.zip",
        )
        db.add(task)
        db.commit()
        db.close()

        response = test_client.get("/api/tasks/missing-file-task/download")
        assert response.status_code == 404
        assert "not found on disk" in response.json()["detail"]

    def test_download_task_no_output_path(self, test_client):
        """测试下载已完成任务但 output_file_path 为空。

        验证：返回状态码 404
        """
        from database import get_db
        db_gen = app.dependency_overrides[get_db]()
        db = next(db_gen)

        # 创建已完成任务但 output_file_path 为空
        task = Task(
            id="no-output-task",
            status="completed",
            progress=100,
            input_text="测试",
            input_image_path="/fake/path/image.png",
            output_file_path=None,
        )
        db.add(task)
        db.commit()
        db.close()

        response = test_client.get("/api/tasks/no-output-task/download")
        assert response.status_code == 404
        assert "not set" in response.json()["detail"]
