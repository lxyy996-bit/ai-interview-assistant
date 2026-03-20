import { useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Loader2, Brain, Search, FileSearch } from 'lucide-react'
import { useStartAnalysis, useSession } from '../hooks/useSession'

export default function AnalysisPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const startAnalysis = useStartAnalysis()
  const { data: session } = useSession(sessionId || '')
  const hasStarted = useRef(false)

  // 自动开始分析（跳转逻辑已在 useStartAnalysis 中处理）
  useEffect(() => {
    if (hasStarted.current) return
    if (sessionId && session && !startAnalysis.isPending && !startAnalysis.isSuccess && !startAnalysis.isError) {
      hasStarted.current = true
      console.log('开始分析，sessionId:', sessionId)
      startAnalysis.mutate(sessionId)
    }
  }, [sessionId, session, startAnalysis])

  const steps = [
    {
      icon: Brain,
      title: '生成搜索关键词',
      description: 'AI 猎头正在分析岗位需求...',
      active: true,
    },
    {
      icon: Search,
      title: '搜集公司情报',
      description: '搜索最新公司动态和业务信息...',
      active: false,
    },
    {
      icon: FileSearch,
      title: '生成分析报告',
      description: 'CHRO 正在深度分析匹配度...',
      active: false,
    },
  ]

  return (
    <div className="max-w-2xl mx-auto text-center">
      <div className="card">
        <Loader2 className="w-16 h-16 text-primary-600 animate-spin mx-auto mb-6" />
        
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          AI 正在分析中...
        </h2>
        <p className="text-gray-600 mb-8">
          这可能需要 30-60 秒，请耐心等待
        </p>

        {/* 分析步骤 */}
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div
              key={index}
              className={`flex items-center p-4 rounded-lg border ${
                step.active
                  ? 'bg-primary-50 border-primary-200'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  step.active
                    ? 'bg-primary-100 text-primary-600'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                <step.icon className="w-5 h-5" />
              </div>
              <div className="ml-4 text-left">
                <h3
                  className={`font-medium ${
                    step.active ? 'text-gray-900' : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </h3>
                <p className="text-sm text-gray-500">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        {startAnalysis.isError && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-600">
              分析过程中出现错误，请刷新页面重试
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
