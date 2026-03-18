import axios, { AxiosResponse } from 'axios'

// API 基础地址 - 使用相对路径，通过 Vite 代理转发
const BASE_URL = '/api/v1'

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
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
  (error) => {
    console.error('API 错误:', error.message, error.response?.data)
    const message = error.response?.data?.error_message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export default api
