import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Users, Plus, LogOut } from 'lucide-react'
import api from '../utils/api'

interface WhitelistItem {
  id: string
  phone: string  // 脱敏手机号
  phone_hash: string
  total_quota: number
  used_quota: number
  remaining_quota: number
  status: string
  remark: string
  created_at: string
  last_used_at: string | null
}

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [whitelist, setWhitelist] = useState<WhitelistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newPhone, setNewPhone] = useState('')
  const [newQuota, setNewQuota] = useState(10)
  const [newRemark, setNewRemark] = useState('')
  const [error, setError] = useState('')

  // 检查管理员登录状态
  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token')
    if (!adminToken) {
      navigate('/manage/login')
      return
    }
    fetchWhitelist()
  }, [navigate])

  const fetchWhitelist = async () => {
    try {
      const token = localStorage.getItem('admin_token')
      const response = await api.get('/admin/whitelist', {
        headers: { Authorization: `Bearer ${token}` }
      }) as any
      
      if (response.code === 0) {
        setWhitelist(response.data.items)
      }
    } catch (err) {
      console.error('获取白名单失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddWhitelist = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    try {
      const token = localStorage.getItem('admin_token')
      const response = await api.post('/admin/whitelist', {
        phone: newPhone,
        total_quota: newQuota,
        remark: newRemark
      }, {
        headers: { Authorization: `Bearer ${token}` }
      }) as any
      
      if (response.code === 0) {
        setShowAddModal(false)
        setNewPhone('')
        setNewQuota(10)
        setNewRemark('')
        fetchWhitelist()
      } else {
        setError(response.message || '添加失败')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || '添加失败')
    }
  }

  const handleUpdateStatus = async (id: string, status: string) => {
    try {
      const token = localStorage.getItem('admin_token')
      await api.put(`/admin/whitelist/${id}/status`, { status }, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchWhitelist()
    } catch (err) {
      console.error('更新状态失败:', err)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个白名单吗？')) return
    
    try {
      const token = localStorage.getItem('admin_token')
      await api.delete(`/admin/whitelist/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchWhitelist()
    } catch (err) {
      console.error('删除失败:', err)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_info')
    navigate('/manage/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-blue-600 mr-3" />
            <h1 className="text-xl font-bold text-gray-900">白名单管理</h1>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900"
          >
            <LogOut className="w-5 h-5 mr-2" />
            退出
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 操作栏 */}
        <div className="mb-6 flex justify-between items-center">
          <div className="text-gray-600">
            共 <span className="font-medium text-gray-900">{whitelist.length}</span> 个白名单
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            <Plus className="w-5 h-5 mr-2" />
            添加白名单
          </button>
        </div>

        {/* 白名单列表 */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  手机号
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  配额
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  备注
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  创建时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {whitelist.map((item) => (
                <tr key={item.id}>
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-sm text-gray-900">
                    {item.phone}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <span className="text-green-600 font-medium">{item.remaining_quota}</span>
                    <span className="text-gray-500"> / {item.total_quota}</span>
                    <span className="text-gray-400 ml-1">(已用 {item.used_quota})</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      item.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {item.status === 'active' ? '正常' : '禁用'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.remark || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleUpdateStatus(item.id, item.status === 'active' ? 'disabled' : 'active')}
                      className={`mr-3 ${item.status === 'active' ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}`}
                    >
                      {item.status === 'active' ? '禁用' : '启用'}
                    </button>
                    <button
                      onClick={() => handleDelete(item.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      删除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>

      {/* 添加白名单弹窗 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-bold text-gray-900 mb-4">添加白名单</h2>
            
            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <form onSubmit={handleAddWhitelist} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  手机号
                </label>
                <input
                  type="tel"
                  value={newPhone}
                  onChange={(e) => setNewPhone(e.target.value)}
                  placeholder="13800138000"
                  maxLength={11}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  配额
                </label>
                <input
                  type="number"
                  value={newQuota}
                  onChange={(e) => setNewQuota(parseInt(e.target.value) || 0)}
                  min={0}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  备注
                </label>
                <input
                  type="text"
                  value={newRemark}
                  onChange={(e) => setNewRemark(e.target.value)}
                  placeholder="可选"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  添加
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
