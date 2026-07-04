/**
 * 应用主组件
 *
 * 提供健康检查和任务提交功能。
 */

import { useState, useRef } from 'react'
import { checkHealth, createTask } from './api'
import './App.css'

/** 健康检查结果状态 */
type HealthStatus = 'idle' | 'loading' | 'success' | 'error'

/** 任务提交状态 */
type TaskStatus = 'idle' | 'submitting' | 'success' | 'error'

function App() {
  // 健康检查相关状态
  const [healthStatus, setHealthStatus] = useState<HealthStatus>('idle')
  const [healthMessage, setHealthMessage] = useState<string>('')

  // 任务提交相关状态
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('idle')
  const [taskId, setTaskId] = useState<string>('')
  const [taskError, setTaskError] = useState<string>('')

  // 表单数据
  const [inputText, setInputText] = useState<string>('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

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
    try {
      const result = await createTask(selectedFile, inputText)
      setTaskStatus('success')
      setTaskId(result.task_id)
    } catch (err) {
      setTaskStatus('error')
      setTaskError(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  /**
   * 重置表单
   */
  const handleReset = () => {
    setTaskStatus('idle')
    setTaskId('')
    setTaskError('')
    setInputText('')
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
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

        {taskStatus === 'success' && (
          <div className="status-message success">
            ✅ 任务创建成功！<br />
            Task ID: <strong>{taskId}</strong>
          </div>
        )}

        {taskStatus === 'error' && (
          <div className="status-message error">
            ❌ {taskError}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
