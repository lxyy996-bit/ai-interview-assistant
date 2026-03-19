import { useMutation, useQuery } from '@tanstack/react-query'
import api from '../utils/api'
import type { CreateSessionRequest, Session, InterviewAnalysis } from '../types'

// 错误提示函数
const showErrorAlert = (message: string) => {
  if (typeof window !== 'undefined') {
    window.alert(message)
  }
}

// API 响应类型
interface ApiResponse<T> {
  success: boolean
  data?: T
  error_message?: string
  error_code?: string
}

// 创建会话
export const useCreateSession = () => {
  return useMutation({
    mutationFn: async (data: CreateSessionRequest) => {
      console.log('发送创建会话请求:', data)
      try {
        const response = await api.post('/sessions', data) as ApiResponse<{ session_id: string }>
        console.log('创建会话响应:', response)
        
        if (!response.success) {
          throw new Error(response.error_message || `创建会话失败: ${response.error_code}`)
        }
        if (!response.data?.session_id) {
          throw new Error('服务器返回数据格式错误')
        }
        return response.data.session_id
      } catch (err: any) {
        console.error('创建会话请求失败:', err)
        showErrorAlert(`创建会话失败: ${err.message}`)
        throw err
      }
    },
  })
}

// 获取会话
export const useSession = (sessionId: string) => {
  return useQuery({
    queryKey: ['session', sessionId],
    queryFn: async () => {
      if (!sessionId) {
        throw new Error('会话ID不能为空')
      }
      try {
        const response = await api.get(`/sessions/${sessionId}`) as ApiResponse<Session>
        if (!response.success) {
          throw new Error(response.error_message || '获取会话失败')
        }
        return response.data!
      } catch (err: any) {
        console.error('获取会话失败:', err)
        // 只在非空 sessionId 时显示错误
        if (sessionId) {
          showErrorAlert(`获取会话失败: ${err.message}`)
        }
        throw err
      }
    },
    enabled: !!sessionId,
  })
}

// 上传简历
export const useUploadResume = () => {
  return useMutation({
    mutationFn: async ({ sessionId, file }: { sessionId: string; file: File }) => {
      try {
        const formData = new FormData()
        formData.append('file', file)
        
        const response = await api.post(`/sessions/${sessionId}/resume`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }) as ApiResponse<{ success: boolean; text_length: number; skills_detected: string[] }>
        
        if (!response.success) {
          throw new Error(response.error_message || '上传简历失败')
        }
        return response.data!
      } catch (err: any) {
        console.error('上传简历失败:', err)
        showErrorAlert(`上传简历失败: ${err.message}`)
        throw err
      }
    },
  })
}

// 开始分析
export const useStartAnalysis = () => {
  return useMutation({
    mutationFn: async (sessionId: string) => {
      try {
        const response = await api.post(`/sessions/${sessionId}/analyze`, {}, {
          timeout: 60000, // 60秒超时
        }) as ApiResponse<InterviewAnalysis>
        
        if (!response.success) {
          throw new Error(response.error_message || '分析失败')
        }
        return response.data!
      } catch (err: any) {
        console.error('分析失败:', err)
        
        // 根据错误类型显示不同提示
        let errorMsg = err.message || '分析失败'
        if (err.name === 'TimeoutError' || err.message?.includes('超时')) {
          errorMsg = '分析请求超时（60秒），服务器响应过慢，请稍后重试'
        } else if (err.name === 'NotFoundError' || err.message?.includes('不存在')) {
          errorMsg = '分析接口未找到，请联系管理员检查后端服务'
        } else if (err.name === 'NetworkError' || err.message?.includes('网络')) {
          errorMsg = '网络连接失败，请检查网络后重试'
        }
        
        showErrorAlert(`分析失败: ${errorMsg}`)
        throw err
      }
    },
  })
}

// 获取分析结果
export const useAnalysisResult = (sessionId: string) => {
  return useQuery({
    queryKey: ['analysis', sessionId],
    queryFn: async () => {
      try {
        const response = await api.get(`/sessions/${sessionId}/result`) as ApiResponse<InterviewAnalysis>
        if (!response.success) {
          throw new Error(response.error_message || '获取结果失败')
        }
        return response.data!
      } catch (err: any) {
        console.error('获取结果失败:', err)
        showErrorAlert(`获取结果失败: ${err.message}`)
        throw err
      }
    },
    enabled: !!sessionId,
  })
}
