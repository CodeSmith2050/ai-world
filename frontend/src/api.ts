/**
 * API 请求封装模块
 *
 * 统一管理后端 API 接口调用，使用 axios 进行 HTTP 请求。
 */

import axios from 'axios'

// 创建 axios 实例，所有请求自动带 /api 前缀
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** 健康检查响应数据类型 */
export interface HealthResponse {
  status: string
}

/** 任务创建响应数据类型 */
export interface TaskCreateResponse {
  task_id: string
  status: string
}

/** 任务状态响应数据类型 */
export interface TaskStatusResponse {
  task_id: string
  status: string
  progress: number
  current_step: string | null
  error_message: string | null
  output_file_path: string | null
  created_at: string
  updated_at: string
}

/**
 * 健康检查接口
 *
 * @returns 服务健康状态
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health')
  return response.data
}

/**
 * 创建任务接口
 *
 * @param image - 上传的图片文件
 * @param text - 输入文本描述
 * @param simulateFailure - 是否模拟失败（可选）
 * @returns 任务创建结果，包含 task_id 和 status
 */
export async function createTask(
  image: File,
  text: string,
  simulateFailure: boolean = false,
): Promise<TaskCreateResponse> {
  const formData = new FormData()
  formData.append('image', image)
  formData.append('text', text)
  if (simulateFailure) {
    formData.append('simulate_failure', 'true')
  }

  const response = await apiClient.post<TaskCreateResponse>('/tasks', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return response.data
}

/**
 * 查询任务状态接口
 *
 * @param taskId - 任务 ID
 * @returns 任务当前状态
 */
export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  const response = await apiClient.get<TaskStatusResponse>(`/tasks/${taskId}`)
  return response.data
}

/**
 * 获取任务结果下载 URL
 *
 * @param taskId - 任务 ID
 * @returns 下载链接
 */
export function getDownloadUrl(taskId: string): string {
  return `/api/tasks/${taskId}/download`
}

export default apiClient
