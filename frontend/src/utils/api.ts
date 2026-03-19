import axios, { AxiosResponse, AxiosError } from 'axios'

// API 基础地址 - 使用相对路径，通过 Vite 代理转发
const BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60秒超时
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API 请求:', config.method?.toUpperCase(), config.url, config.data)
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器 - 直接返回 data
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('API 响应:', response.status, response.data)
    return response.data
  },
  (error: AxiosError) => {
    console.error('API 错误:', error.message, error.response?.data)
    
    // 处理超时错误
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      const timeoutError = new Error('请求超时，请稍后重试')
      timeoutError.name = 'TimeoutError'
      return Promise.reject(timeoutError)
    }
    
    // 处理网络错误
    if (error.code === 'ERR_NETWORK' || error.message?.includes('Network Error')) {
      const networkError = new Error('网络连接失败，请检查网络后重试')
      networkError.name = 'NetworkError'
      return Promise.reject(networkError)
    }
    
    // 处理 404 错误
    if (error.response?.status === 404) {
      const notFoundError = new Error('请求的资源不存在，请稍后重试')
      notFoundError.name = 'NotFoundError'
      return Promise.reject(notFoundError)
    }
    
    // 其他错误
    const message = (error.response?.data as any)?.error_message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default api
