/**
 * 应用主组件
 *
 * 提供健康检查、任务提交、任务进度跟踪功能。
 */

import { useState, useRef, useEffect } from 'react'
import {
  checkHealth,
  createTask,
  getTaskStatus,
  getDownloadUrl,
  type TaskStatusResponse,
} from './api'
import './App.css'

/** 健康检查结果状态 */
type HealthStatus = 'idle' | 'loading' | 'success' | 'error'

/** 任务提交状态 */
type TaskStatus = 'idle' | 'submitting' | 'success' | 'error'

/** 轮询间隔（毫秒） */
const POLL_INTERVAL = 2000

function App() {
  // 健康检查相关状态
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('idle')
  const [healthMessage, setHealthMessage] = useState<string>('')

  // 任务提交相关状态
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle')
  const [taskId, setTaskId] = useState<string>('')
  const [taskError, setTaskError] = useState<string>('')

  // 任务进度跟踪状态
  const [taskProgress, setTaskProgress] = useState<TaskStatusResponse | null>(null)

  // 表单数据
  const [inputText, setInputText] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 轮询定时器引用
  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  /**
   * 停止轮询
   */
  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
  }

  /**
   * 开始轮询任务状态
   *
   * 每 2 秒查询一次任务状态，直到任务完成或失败。
   *
   * @param id - 任务 ID
   */
  const startPolling = (id: string) => {
    const poll = async () => {
      try {
        const status = await getTaskStatus(id)
        setTaskProgress(status)

        // 任务完成或失败时停止轮询
        if (status.status === 'completed' || status.status === 'failed') {
          stopPolling()
          return
        }
      } catch (err) {
        // 请求失败时停止轮询
        stopPolling()
        return
      }

      // 继续下一轮轮询
      pollTimerRef.current = setTimeout(poll, POLL_INTERVAL)
    }

    poll()
  }

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => stopPolling()
  }, [])

  /**
   * 处理健康检查按钮点击事件
   */
  const handleHealthCheck = async () => {
    setHealthStatus('loading')
    setHealthMessage('')
    try {
      const result = await checkHealth()
      setHealthStatus('success')
      setHealthMessage(result.status)
    } catch (err) {
      setHealthStatus('error')
      setHealthMessage(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  /**
   * 处理文件选择
   */
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  /**
   * 处理任务提交
   */
  const handleSubmitTask = async () => {
    if (!selectedFile || !inputText.trim()) {
      setTaskStatus('error')
      setTaskError('Please select an image and enter text description')
      return
    }

    setTaskStatus('submitting')
    setTaskError('')
    setTaskProgress(null)
    try {
      const result = await createTask(selectedFile, inputText, simulateFailure)
      setTaskStatus('success')
      setTaskId(result.task_id)
      // 开始轮询任务状态
      startPolling(result.task_id)
    } catch (err) {
      setTaskStatus('error')
      setTaskError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  /**
   * 重置表单
   */
  const handleReset = () => {
    stopPolling()
    setTaskStatus('idle')
    setTaskId('')
    setTaskError('')
    setTaskProgress(null)
    setInputText('')
    setSelectedFile(null)
    setSimulateFailure(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  /**
   * 处理下载结果
   */
  const handleDownload = () => {
    if (taskId) {
      window.open(getDownloadUrl(taskId), '_blank')
    }
  }

  /** 获取状态文案 */
  const getStatusText = (status: string): string => {
    const statusMap: Record<string, string> = {
      queued: '排队中',
      processing: '处理中',
      completed: '已完成',
      failed: '失败',
    }
    return statusMap[status] || status
  }

  return (
    <div className="app-container">
      <h1>AI World 技术服务平台</h1>
      <p className="subtitle">从图片+文本到 3D 模型生成与仿真计算</p>

      {/* 健康检查区域 */}
      <div className="health-section">
        <h2>健康检查</h2>
        <button
          type="button"
          className="health-button"
          onClick={handleHealthCheck}
          disabled={healthStatus === 'loading'}
        >
          {healthStatus === 'loading' ? '检查中...' : '检查服务状态'}
        </button>

        {healthStatus === 'success' && (
          <div className="status-message success">
            ✅ 服务状态: <strong>{healthMessage}</strong>
          </div>
        )}

        {healthStatus === 'error' && (
          <div className="status-message error">
            ❌ 请求失败: <strong>{healthMessage}</strong>
          </div>
        )}
      </div>

      {/* 任务提交区域 */}
      <div className="task-section">
        <h2>创建任务</h2>

        <div className="form-group">
          <label htmlFor="file-input" className="form-label">
            选择图片
          </label>
          <input
            id="file-input"
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="file-input"
          />
          {selectedFile && (
            <p className="file-name">已选择: {selectedFile.name}</p>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="text-input" className="form-label">
            文本描述
          </label>
          <textarea
            id="text-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="请输入您的需求描述..."
            className="text-input"
            rows={4}
          />
        </div>

        <div className="form-group checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
            />
            模拟失败（测试用）
          </label>
        </div>

        <div className="button-group">
          <button
            type="button"
            className="submit-button"
            onClick={handleSubmitTask}
            disabled={taskStatus === 'submitting'}
          >
            {taskStatus === 'submitting' ? '提交中...' : '提交任务'}
          </button>
          {taskStatus !== 'idle' && (
            <button
              type="button"
              className="reset-button"
              onClick={handleReset}
            >
              重置
            </button>
          )}
        </div>

        {taskStatus === 'error' && (
          <div className="status-message error">
            ❌ {taskError}
          </div>
        )}
      </div>

      {/* 任务进度区域 */}
      {taskProgress && (
        <div className="progress-section">
          <h2>任务进度</h2>

          <div className="progress-info">
            <div className="progress-row">
              <span className="progress-label">Task ID:</span>
              <span className="progress-value">{taskProgress.task_id}</span>
            </div>
            <div className="progress-row">
              <span className="progress-label">状态:</span>
              <span className={`progress-value status-badge ${taskProgress.status}`}>
                {getStatusText(taskProgress.status)}
              </span>
            </div>
            {taskProgress.current_step && (
              <div className="progress-row">
                <span className="progress-label">当前步骤:</span>
                <span className="progress-value">{taskProgress.current_step}</span>
              </div>
            )}
          </div>

          {/* 进度条 */}
          <div className="progress-bar-container">
            <div
              className="progress-bar-fill"
              style={{ width: `${taskProgress.progress}%` }}
            />
            <span className="progress-bar-text">{taskProgress.progress}%</span>
          </div>

          {/* 下载按钮 */}
          {taskProgress.status === 'completed' && (
            <div className="download-section">
              <button
                type="button"
                className="download-button"
                onClick={handleDownload}
              >
                📥 下载结果
              </button>
            </div>
          )}

          {/* 错误信息 */}
          {taskProgress.status === 'failed' && taskProgress.error_message && (
            <div className="status-message error">
              ❌ 错误: {taskProgress.error_message}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default App
