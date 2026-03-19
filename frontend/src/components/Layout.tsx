import { useState, useEffect } from 'react'
import { Sparkles, User, LogOut, Ticket } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'

interface LayoutProps {
  children: React.ReactNode
}

interface UserInfo {
  phone_masked: string
  total_quota: number
  used_quota: number
  remaining_quota: number
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)

  useEffect(() => {
    // 从 localStorage 获取用户信息
    const stored = localStorage.getItem('user_info')
    if (stored) {
      setUserInfo(JSON.parse(stored))
    }
    
    // 获取最新配额信息
    fetchQuota()
  }, [])

  const fetchQuota = async () => {
    try {
      const response = await api.get('/auth/quota') as any
      if (response.code === 0 && response.data) {
        setUserInfo(prev => ({
          ...prev,
          ...response.data
        }))
      }
    } catch (err) {
      console.error('获取配额失败:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">AI 智能面试助手</h1>
            </div>
            
            {/* 用户信息 */}
            {userInfo && (
              <div className="flex items-center space-x-6">
                {/* 次数信息 */}
                <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-lg">
                  <Ticket className="w-5 h-5 text-blue-600" />
                  <span className="text-sm text-gray-600">
                    剩余 <span className="font-bold text-blue-600">{userInfo.remaining_quota}</span> 次
                  </span>
                  <span className="text-gray-400">|</span>
                  <span className="text-sm text-gray-500">
                    总计 {userInfo.total_quota} 次
                  </span>
                </div>
                
                {/* 手机号 */}
                <div className="flex items-center space-x-2 text-gray-600">
                  <User className="w-5 h-5" />
                  <span className="text-sm">{userInfo.phone_masked}</span>
                </div>
                
                {/* 退出按钮 */}
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 text-gray-500 hover:text-red-600 transition-colors"
                >
                  <LogOut className="w-5 h-5" />
                  <span className="text-sm">退出</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-center text-sm text-gray-500">
            AI 智能面试助手 © 2026 - 基于 STAR 法则的面试准备系统
          </p>
        </div>
      </footer>
    </div>
  )
}
