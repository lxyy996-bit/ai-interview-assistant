import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Briefcase, Building2, MapPin, FileText } from 'lucide-react'
import { useCreateSession } from '../hooks/useSession'

export default function HomePage() {
  const navigate = useNavigate()
  const createSession = useCreateSession()
  
  const [formData, setFormData] = useState({
    company: '',
    job_name: '',
    jd: '',
    city: '',
  })
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    
    console.log('表单提交:', formData)
    
    try {
      const sessionId = await createSession.mutateAsync(formData)
      console.log('会话创建成功:', sessionId)
      navigate(`/upload/${sessionId}`)
    } catch (err) {
      console.error('创建会话失败:', err)
      setError(err instanceof Error ? err.message : '创建会话失败，请重试')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          准备你的面试
        </h2>
        <p className="text-gray-600">
          输入目标公司和岗位信息，AI 将为你生成个性化的面试准备方案
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 错误提示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600 text-sm">{error}</p>
            </div>
          )}

          {/* 目标公司 */}
          <div>
            <label className="label flex items-center space-x-2">
              <Building2 className="w-4 h-4" />
              <span>目标公司</span>
            </label>
            <input
              type="text"
              className="input"
              placeholder="例如：字节跳动、阿里巴巴"
              value={formData.company}
              onChange={(e) => setFormData({ ...formData, company: e.target.value })}
              required
            />
          </div>

          {/* 岗位名称 */}
          <div>
            <label className="label flex items-center space-x-2">
              <Briefcase className="w-4 h-4" />
              <span>岗位名称</span>
            </label>
            <input
              type="text"
              className="input"
              placeholder="例如：高级产品经理"
              value={formData.job_name}
              onChange={(e) => setFormData({ ...formData, job_name: e.target.value })}
              required
            />
          </div>

          {/* 工作地点 */}
          <div>
            <label className="label flex items-center space-x-2">
              <MapPin className="w-4 h-4" />
              <span>工作地点</span>
            </label>
            <input
              type="text"
              className="input"
              placeholder="例如：北京、上海"
              value={formData.city}
              onChange={(e) => setFormData({ ...formData, city: e.target.value })}
              required
            />
          </div>

          {/* 岗位要求 */}
          <div>
            <label className="label flex items-center space-x-2">
              <FileText className="w-4 h-4" />
              <span>岗位要求 / JD</span>
            </label>
            <textarea
              className="input h-32 resize-none"
              placeholder="粘贴岗位描述（JD）内容..."
              value={formData.jd}
              onChange={(e) => setFormData({ ...formData, jd: e.target.value })}
              required
            />
          </div>

          {/* 提交按钮 */}
          <button
            type="submit"
            className="w-full btn-primary py-3"
            disabled={createSession.isPending}
          >
            {createSession.isPending ? (
              <span className="flex items-center justify-center space-x-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>创建中...</span>
              </span>
            ) : (
              '下一步：上传简历'
            )}
          </button>
        </form>
      </div>

      {/* 功能介绍 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Building2 className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold mb-1">公司情报分析</h3>
          <p className="text-sm text-gray-600">基于最新公开信息分析公司战略方向</p>
        </div>
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <FileText className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold mb-1">智能简历评分</h3>
          <p className="text-sm text-gray-600">评估简历与岗位的匹配度和优化建议</p>
        </div>
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-3">
            <Briefcase className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold mb-1">STAR 面试题</h3>
          <p className="text-sm text-gray-600">生成个性化的 STAR 法则面试问题</p>
        </div>
      </div>
    </div>
  )
}
