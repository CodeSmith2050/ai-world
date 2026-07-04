"""Pydantic 数据模型（Schema）定义模块。

定义 API 请求与响应的数据结构，用于数据验证与序列化。
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TaskCreateResponse(BaseModel):
    """任务创建响应模型。

    Attributes:
        task_id: 新创建任务的 ID。
        status: 任务初始状态。
    """

    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """任务状态查询响应模型。

    Attributes:
        task_id: 任务 ID。
        status: 当前任务状态。
        progress: 当前进度百分比。
        current_step: 当前执行步骤描述。
        error_message: 错误信息（仅失败时有值）。
        output_file_path: 输出文件路径（仅完成时有值）。
        created_at: 任务创建时间。
        updated_at: 任务更新时间。
    """

    task_id: str = Field(alias="id")
    status: str
    progress: int
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    output_file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class HealthResponse(BaseModel):
    """健康检查响应模型。

    Attributes:
        status: 服务状态，正常时为 "ok"。
    """

    status: str = Field(default="ok", description="Service health status")
