import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Phone, ArrowRight, AlertCircle } from 'lucide-react'
import api from '../utils/api'

export default function LoginPage() {
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const response = await api.post('/auth/login', { phone }) as any
      
      if (response.code === 0 && response.data) {
        // 保存 token
        localStorage.setItem('access_token', response.data.access_token)
        localStorage.setItem('user_info', JSON.stringify(response.data.user))
        
        // 跳转到首页
        navigate('/')
      } else {
        setError(response.message || '登录失败')
      }
    } catch (err: any) {
      console.error('登录失败:', err)
      // 优先使用后端返回的错误信息
      const detail = err.response?.data?.detail
      let errorMsg = '登录失败'
      
      if (typeof detail === 'object' && detail.message) {
        // 后端返回的结构化错误
        errorMsg = detail.message
      } else if (typeof detail === 'string') {
        // 后端返回的字符串错误
        errorMsg = detail
      } else if (err.message) {
        errorMsg = err.message
      }
      
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-full max-w-md p-8 bg-white rounded-2xl shadow-xl">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Phone className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">AI 面试助手</h1>
          <p className="text-gray-600 mt-2">请输入手机号登录</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mr-2 flex-shrink-0 mt-0.5" />
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              手机号
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="请输入11位手机号"
              maxLength={11}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || phone.length !== 11}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                登录
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            未授权用户请联系管理员添加白名单
          </p>
        </div>


      </div>
    </div>
  )
}
