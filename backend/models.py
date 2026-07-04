"""SQLAlchemy 数据模型定义模块。

定义任务（Task）模型及其相关字段结构。
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime

from database import Base


def generate_uuid() -> str:
    """生成 UUID 字符串作为主键。

    Returns:
        str: 不带连字符的 UUID 字符串。
    """
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """获取当前 UTC 时间。

    Returns:
        datetime: 当前 UTC 时间的 datetime 对象。
    """
    return datetime.now(timezone.utc)


class Task(Base):
    """任务模型，表示一个从输入到输出的处理任务。

    Attributes:
        id: 任务唯一标识符，UUID 格式。
        status: 任务状态，可选值 queued/processing/completed/failed。
        progress: 任务进度百分比，0-100。
        input_text: 输入的文本描述。
        input_image_path: 上传图片的存储路径。
        output_file_path: 输出结果文件的存储路径，可为空。
        error_message: 错误信息，任务失败时记录，可为空。
        current_step: 当前执行步骤描述，可为空。
        created_at: 任务创建时间。
        updated_at: 任务最后更新时间。
    """

    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    status = Column(String, default="queued", index=True)
    progress = Column(Integer, default=0)
    input_text = Column(Text, nullable=False)
    input_image_path = Column(String, nullable=False)
    output_file_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    current_step = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
