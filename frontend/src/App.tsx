/**
 * 应用主组件
 *
 * 提供健康检查功能，验证前后端通信是否正常。
 */

import { useState } from 'react'
import { checkHealth } from './api'
import './App.css'

/**
 * 健康检查结果状态
 *
 * idle: 初始状态
 * loading: 请求中
 * success: 请求成功
 * error: 请求失败
 */
type HealthStatus = 'idle' | 'loading' | 'success' | 'error'

function App() {
  const [status, setStatus] = useState<HealthStatus>('idle')
  const [message, setMessage] = useState<string>('')

  /**
   * 处理健康检查按钮点击事件
   *
   * 调用后端健康检查接口，更新状态与显示信息。
   */
  const handleHealthCheck = async () => {
    setStatus('loading')
    setMessage('')
    try {
      const result = await checkHealth()
      setStatus('success')
      setMessage(result.status)
    } catch (err) {
      setStatus('error')
      setMessage(err instanceof Error ? err.message : 'Unknown error')
    }
  }

  return (
    <div className="app-container">
      <h1>AI World 技术服务平台</h1>
      <p className="subtitle">从图片+文本到 3D 模型生成与仿真计算</p>

      <div className="health-section">
        <h2>健康检查</h2>
        <button
          type="button"
          className="health-button"
          onClick={handleHealthCheck}
          disabled={status === 'loading'}
        >
          {status === 'loading' ? '检查中...' : '检查服务状态'}
        </button>

        {status === 'success' && (
          <div className="status-message success">
            ✅ 服务状态: <strong>{message}</strong>
          </div>
        )}

        {status === 'error' && (
          <div className="status-message error">
            ❌ 请求失败: <strong>{message}</strong>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
