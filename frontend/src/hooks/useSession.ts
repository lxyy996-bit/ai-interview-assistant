import { useMutation, useQuery } from '@tanstack/react-query'
import api from '../utils/api'
import type { CreateSessionRequest, Session, InterviewAnalysis } from '../types'

// 创建会话
export const useCreateSession = () => {
  return useMutation({
    mutationFn: async (data: CreateSessionRequest) => {
      console.log('发送创建会话请求:', data)
      try {
        const response = await api.post('/sessions', data) as { success: boolean; data?: { session_id: string }; error_message?: string; error_code?: string }
        console.log('创建会话响应:', response)
        
        if (!response.success) {
          throw new Error(response.error_message || `创建会话失败: ${response.error_code}`)
        }
        if (!response.data?.session_id) {
          throw new Error('服务器返回数据格式错误')
        }
        return response.data.session_id
      } catch (err) {
        console.error('创建会话请求失败:', err)
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
      const response = await api.get(`/sessions/${sessionId}`) as { success: boolean; data?: Session; error_message?: string }
      if (!response.success) {
        throw new Error(response.error_message || '获取会话失败')
      }
      return response.data!
    },
    enabled: !!sessionId,
  })
}

// 上传简历
export const useUploadResume = () => {
  return useMutation({
    mutationFn: async ({ sessionId, file }: { sessionId: string; file: File }) => {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post(`/sessions/${sessionId}/resume`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }) as { success: boolean; data?: { success: boolean; text_length: number; skills_detected: string[] }; error_message?: string }
      
      if (!response.success) {
        throw new Error(response.error_message || '上传简历失败')
      }
      return response.data!
    },
  })
}

// 开始分析
export const useStartAnalysis = () => {
  return useMutation({
    mutationFn: async (sessionId: string) => {
      const response = await api.post(`/sessions/${sessionId}/analyze`) as { success: boolean; data?: InterviewAnalysis; error_message?: string }
      if (!response.success) {
        throw new Error(response.error_message || '分析失败')
      }
      return response.data!
    },
  })
}

// 获取分析结果
export const useAnalysisResult = (sessionId: string) => {
  return useQuery({
    queryKey: ['analysis', sessionId],
    queryFn: async () => {
      const response = await api.get(`/sessions/${sessionId}/result`) as { success: boolean; data?: InterviewAnalysis; error_message?: string }
      if (!response.success) {
        throw new Error(response.error_message || '获取结果失败')
      }
      return response.data!
    },
    enabled: !!sessionId,
  })
}
