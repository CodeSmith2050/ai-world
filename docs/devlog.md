# 开发日志

## 阶段0：项目初始化

### 日期
2026-07-04

### 阶段目标
搭建最小可运行骨架，前后端能通信。验证从前端发起请求到后端响应的完整链路。

### 关键代码修改（文件列表）

#### 后端 (backend/)
- `pyproject.toml` - 使用 uv 管理依赖，包含 fastapi, uvicorn, celery, redis, sqlalchemy, aiofiles, python-multipart, pydantic
- `uv.lock` - 依赖锁定文件（自动生成）
- `database.py` - SQLite 数据库连接配置，提供引擎、SessionLocal 和 Base
- `models.py` - SQLAlchemy Task 模型定义（预留阶段1使用）
- `schemas.py` - Pydantic 模型定义（HealthResponse, TaskCreateResponse, TaskStatusResponse）
- `main.py` - FastAPI 应用入口，包含 /api/health 健康检查端点

#### 前端 (frontend/)
- `package.json` - Vite + React + TypeScript 项目，添加 axios 依赖
- `vite.config.ts` - 配置 /api 代理到 http://localhost:8000
- `src/api.ts` - API 请求封装，axios 实例和健康检查接口
- `src/App.tsx` - 主应用组件，健康检查按钮与状态展示
- `src/App.css` - 页面样式

#### 项目目录
- `media/uploads/` - 上传文件存储目录
- `media/results/` - 结果文件存储目录
- `docs/test_report_stage0.md` - 阶段0测试报告

### 遇到的问题及解决方案

**问题1：uv init 默认 Python 版本过高**
- 现象：`uv init` 生成的 pyproject.toml 中 `requires-python = ">=3.14"`
- 解决方案：手动修改为 `>=3.10`，兼容更多 Python 版本

**问题2：backend 目录已存在时 uv init 的处理**
- 现象：我们先手动创建了 backend 目录，再执行 uv init
- 解决方案：直接在已有的 backend 目录中执行 `uv init`，成功创建项目

**问题3：硬链接失败警告**
- 现象：`uv sync` 时出现 "Failed to hardlink files; falling back to full copy" 警告
- 原因：缓存目录和目标目录在不同文件系统上
- 解决方案：不影响功能，仅性能略降，可忽略

### 技术栈确认
- **后端**: Python 3.10+ / FastAPI / SQLAlchemy / SQLite / Celery / Redis
- **包管理**: uv（pyproject.toml + uv.lock）
- **前端**: Vite / React 18 / TypeScript / axios
- **构建工具**: Vite

### 提交信息
- 提交说明: `feat: init project skeleton with health check`
- 提交 Hash: `3975e83`
- 分支: dev

---

## 阶段1：任务创建与数据库集成

### 日期
2026-07-04

### 阶段目标
实现 POST /api/tasks 接口，接收图片和文本，写入数据库，返回 task_id。

### 关键代码修改（文件列表）

#### 后端 (backend/)
- `pyproject.toml` - 添加 pytest、httpx 开发依赖，配置 pytest pythonpath
- `main.py` - 新增 POST /api/tasks 端点，实现文件上传和数据库写入
- `schemas.py` - 修复 Pydantic V2 弃用警告（class Config -> model_config）
- `tests/test_tasks.py` - 新增 6 个单元测试用例

#### 前端 (frontend/)
- `src/api.ts` - 新增 createTask、getTaskStatus、getDownloadUrl 接口
- `src/App.tsx` - 新增任务提交表单（文件选择、文本输入、提交按钮）
- `src/App.css` - 新增表单相关样式

#### 文档
- `docs/test_report_stage1.md` - 阶段1测试报告

### 遇到的问题及解决方案

**问题1：pytest 模块导入失败**
- 现象：`ModuleNotFoundError: No module named 'database'`
- 原因：pytest 未配置 pythonpath
- 解决方案：在 pyproject.toml 中添加 `[tool.pytest.ini_options]` 配置 `pythonpath = ["."]`

**问题2：Pydantic V2 弃用警告**
- 现象：`Support for class-based config is deprecated`
- 解决方案：将 `class Config: from_attributes = True` 改为 `model_config = ConfigDict(from_attributes=True)`

### 测试结果
- 6 个单元测试全部通过（6 passed）
- 前端 TypeScript 类型检查通过

### 提交信息
- 提交说明: `feat: add task creation endpoint with file upload and database`
- 分支: dev
