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

---

## 阶段2：异步任务与 Celery 集成

### 日期
2026-07-04

### 阶段目标
任务创建后自动触发 Celery 异步任务处理，更新任务状态，前端实时展示进度。

### 关键代码修改（文件列表）

#### 后端 (backend/)
- `celery_app.py` - 新建，Celery 应用配置，支持 Redis broker 和测试内存 broker
- `tasks.py` - 新建，process_task 异步任务实现（解析需求→生成3D模型→仿真计算→完成）
- `main.py` - 添加 simulate_failure 参数，创建任务后调用 process_task.delay()，新增 GET /api/tasks/{task_id} 状态查询接口
- `schemas.py` - 修复 TaskStatusResponse 字段映射（使用 alias="id" 映射 task_id）
- `tests/test_celery.py` - 新建，4 个 Celery 任务单元测试
- `tests/test_tasks.py` - 更新，使用 mock 隔离 Celery 依赖

#### 前端 (frontend/)
- `src/api.ts` - 新增 getTaskStatus、getDownloadUrl 接口和 TaskStatusResponse 类型
- `src/App.tsx` - 新增任务进度轮询逻辑（2秒间隔）、进度条展示、下载按钮、错误展示
- `src/App.css` - 新增进度条、状态徽章、下载按钮等样式

#### 文档
- `docs/test_report_stage2.md` - 阶段2测试报告

### 遇到的问题及解决方案

**问题1：Celery eager 模式仍连接 Redis**
- 现象：设置了 task_always_eager=True 但 Celery backend 仍尝试连接 Redis
- 原因：Celery 配置的 backend 仍指向 Redis
- 解决方案：在 celery_app.py 中添加 IS_TESTING 环境变量判断，测试时使用 memory broker 和 cache backend

**问题2：TaskStatusResponse 字段映射错误**
- 现象：`Field required [type=missing]` for task_id
- 原因：SQLAlchemy 模型字段名为 `id`，但 Pydantic schema 中为 `task_id`
- 解决方案：使用 `Field(alias="id")` 和 `populate_by_name=True` 配置

**问题3：测试中 Celery 任务连接 Redis 超时**
- 现象：test_tasks.py 中的测试因 Celery.delay() 连接 Redis 失败
- 解决方案：使用 `@patch("main.process_task")` mock 掉 Celery 任务调用

### 测试结果
- 10 个单元测试全部通过（10 passed）
- 前端 TypeScript 类型检查通过

### 提交信息
- 提交说明: `feat: add celery task with mock processing and status polling`
- 分支: dev

---

## 阶段3：结果下载与错误处理

### 日期
2026-07-04

### 阶段目标
实现结果文件下载接口，前端展示下载按钮和失败错误信息。

### 关键代码修改（文件列表）

#### 后端 (backend/)
- `main.py` - 新增 GET /api/tasks/{task_id}/download 下载端点，支持文件流返回
  - 任务不存在返回 404
  - 任务未完成返回 400
  - output_file_path 为空返回 404
  - 文件不存在返回 404
  - 正常返回 FileResponse（application/zip）
- `tests/test_download.py` - 新建，5 个下载接口单元测试

#### 前端 (frontend/)
- 前端下载按钮、失败展示、模拟失败复选框已在阶段2实现，本阶段无需修改

#### 文档
- `docs/test_report_stage3.md` - 阶段3测试报告

### 遇到的问题及解决方案

无新问题，阶段2已提前实现了前端的下载按钮和错误展示逻辑。

### 测试结果
- 15 个单元测试全部通过（15 passed）
- 前端 TypeScript 类型检查通过

### 提交信息
- 提交说明: `feat: add download endpoint and error display`
- 分支: dev
