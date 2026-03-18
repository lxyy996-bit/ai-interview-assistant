import { useParams } from 'react-router-dom'
import { 
  Building2, 
  Target, 
  FileEdit, 
  HelpCircle,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Lightbulb
} from 'lucide-react'
import { useAnalysisResult, useSession } from '../hooks/useSession'

export default function ResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const { data: analysis, isLoading } = useAnalysisResult(sessionId || '')
  const { data: session } = useSession(sessionId || '')

  if (isLoading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full mx-auto" />
        <p className="mt-4 text-gray-600">加载结果中...</p>
      </div>
    )
  }

  if (!analysis) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-600">分析结果不存在</p>
      </div>
    )
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBg = (score: number) => {
    if (score >= 80) return 'bg-green-100'
    if (score >= 60) return 'bg-yellow-100'
    return 'bg-red-100'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 头部信息 */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              面试分析报告
            </h2>
            {session && (
              <p className="text-gray-600 mt-1">
                {session.company} · {session.job_name} · {session.city}
              </p>
            )}
          </div>
          <div className={`px-6 py-4 rounded-xl ${getScoreBg(analysis.ats_score.score)}`}>
            <p className="text-sm text-gray-600">匹配度评分</p>
            <p className={`text-4xl font-bold ${getScoreColor(analysis.ats_score.score)}`}>
              {analysis.ats_score.score}
            </p>
          </div>
        </div>
      </div>

      {/* 公司战略意图解码 */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Building2 className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">公司战略意图解码</h3>
        </div>
        
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">业务现状</h4>
            <p className="text-gray-600 leading-relaxed">
              {analysis.company_strategy.business_status}
            </p>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">岗位"潜台词"</h4>
            <p className="text-gray-600 leading-relaxed">
              {analysis.company_strategy.job_subtext}
            </p>
          </div>
        </div>
      </div>

      {/* ATS 战略匹配评分 */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Target className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">ATS 战略匹配评分</h3>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 优势点 */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <TrendingUp className="w-4 h-4 text-green-600" />
              <h4 className="font-medium text-gray-900">优势点</h4>
            </div>
            <ul className="space-y-2">
              {analysis.ats_score.advantages.map((advantage: string, index: number) => (
                <li key={index} className="flex items-start space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-600">{advantage}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {/* 致命缺口 */}
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-red-600" />
              <h4 className="font-medium text-gray-900">致命缺口</h4>
            </div>
            <ul className="space-y-2">
              {analysis.ats_score.gaps.map((gap: string, index: number) => (
                <li key={index} className="flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" />
                  <span className="text-gray-600">{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* 简历修改建议 */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <FileEdit className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">简历修改建议</h3>
        </div>
        
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Lightbulb className="w-4 h-4 text-blue-600" />
              <h4 className="font-medium text-blue-900">修改逻辑</h4>
            </div>
            <p className="text-blue-800">{analysis.resume_suggestions.logic}</p>
          </div>
          
          <div className="border rounded-lg overflow-hidden">
            <div className="bg-gray-50 px-4 py-2 border-b">
              <h4 className="font-medium text-gray-700">改写示范</h4>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">原描述</p>
                <p className="text-gray-700 bg-gray-100 rounded p-3">
                  {analysis.resume_suggestions.rewrite_demo.original}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">战略化改写</p>
                <p className="text-gray-700 bg-green-50 border border-green-200 rounded p-3">
                  {analysis.resume_suggestions.rewrite_demo.rewritten}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">改写逻辑</p>
                <p className="text-gray-600 text-sm">
                  {analysis.resume_suggestions.rewrite_demo.reasoning}
                </p>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">建议新增关键词</h4>
            <div className="flex flex-wrap gap-2">
              {analysis.resume_suggestions.new_keywords.map((keyword: string, index: number) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* STAR 深度提问 */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <HelpCircle className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold">STAR 深度提问</h3>
        </div>
        
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
          <p className="text-amber-800 text-sm">
            <span className="font-medium">提问背景：</span>
            {analysis.star_questions.background}
          </p>
        </div>
        
        <div className="space-y-4">
          {analysis.star_questions.questions.map((question: string, index: number) => (
            <div key={index} className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                {index + 1}
              </span>
              <p className="text-gray-700 leading-relaxed">{question}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 底部操作 */}
      <div className="flex justify-center space-x-4 pb-8">
        <button
          onClick={() => window.print()}
          className="btn-secondary"
        >
          打印报告
        </button>
        <button
          onClick={() => window.location.href = '/'}
          className="btn-primary"
        >
          开始新的分析
        </button>
      </div>
    </div>
  )
}
