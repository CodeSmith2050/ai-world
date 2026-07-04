"""数据库连接与会话管理模块。

使用 SQLAlchemy 管理 SQLite 数据库连接，提供会话工厂与基础模型类。
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库文件路径，放在项目根目录下
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'app.db'}"

# 创建数据库引擎
# check_same_thread=False 是 SQLite 多线程访问的必需配置
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明式基类，所有模型继承此类
Base = declarative_base()


def get_db():
    """获取数据库会话的依赖注入函数。

    Yields:
        Session: 数据库会话对象，使用完毕后自动关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
