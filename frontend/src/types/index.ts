// 会话相关
export interface Session {
  id: string
  company: string
  job_name: string
  city: string
  has_resume: boolean
  has_analysis: boolean
  created_at: string
  updated_at: string
}

export interface CreateSessionRequest {
  company: string
  job_name: string
  jd: string
  city: string
}

// 分析结果相关
export interface CompanyStrategy {
  business_status: string
  job_subtext: string
}

export interface ATSScore {
  score: number
  advantages: string[]
  gaps: string[]
}

export interface RewriteDemo {
  original: string
  rewritten: string
  reasoning: string
}

export interface ResumeSuggestions {
  logic: string
  rewrite_demo: RewriteDemo
  new_keywords: string[]
}

export interface STARQuestions {
  background: string
  questions: string[]
}

export interface InterviewAnalysis {
  company_strategy: CompanyStrategy
  ats_score: ATSScore
  resume_suggestions: ResumeSuggestions
  star_questions: STARQuestions
}

// API 响应
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error_code?: string
  error_message?: string
}
