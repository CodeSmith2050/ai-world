/**
 * API 请求封装模块
 *
 * 统一管理后端 API 接口调用，使用 axios 进行 HTTP 请求。
 */

import axios from 'axios'

// 创建 axios 实例，所有请求自动带 /api 前缀
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** 健康检查响应数据类型 */
export interface HealthResponse {
  status: string
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

export default apiClient
