import { useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Upload, File, X, CheckCircle } from 'lucide-react'
import { useUploadResume, useSession } from '../hooks/useSession'

export default function UploadPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const uploadResume = useUploadResume()
  const { data: session } = useSession(sessionId || '')
  
  const [dragActive, setDragActive] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (validateFile(file)) {
        setSelectedFile(file)
      }
    }
  }, [])

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (validateFile(file)) {
        setSelectedFile(file)
      }
    }
  }

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]
    
    if (!allowedTypes.includes(file.type)) {
      alert('仅支持 PDF 和 Word 格式')
      return false
    }
    
    if (file.size > 10 * 1024 * 1024) {
      alert('文件大小不能超过 10MB')
      return false
    }
    
    return true
  }

  const handleUpload = async () => {
    if (!selectedFile || !sessionId) return
    
    try {
      await uploadResume.mutateAsync({ sessionId, file: selectedFile })
      navigate(`/analysis/${sessionId}`)
    } catch (error) {
      console.error('上传失败:', error)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      {/* 进度指示器 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              <CheckCircle className="w-5 h-5" />
            </div>
            <span className="ml-2 text-sm font-medium text-gray-900">填写信息</span>
          </div>
          <div className="flex-1 h-1 bg-primary-600 mx-4" />
          <div className="flex items-center">
            <div className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
              2
            </div>
            <span className="ml-2 text-sm font-medium text-gray-900">上传简历</span>
          </div>
          <div className="flex-1 h-1 bg-gray-300 mx-4" />
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-300 text-gray-600 rounded-full flex items-center justify-center text-sm font-medium">
              3
            </div>
            <span className="ml-2 text-sm text-gray-500">分析结果</span>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-xl font-bold mb-4">上传你的简历</h2>
        
        {session && (
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-600">
              <p><span className="font-medium">目标公司：</span>{session.company}</p>
              <p><span className="font-medium">岗位名称：</span>{session.job_name}</p>
              <p><span className="font-medium">工作地点：</span>{session.city}</p>
            </div>
          </div>
        )}

        {/* 上传区域 */}
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragActive
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            type="file"
            id="resume-upload"
            className="hidden"
            accept=".pdf,.doc,.docx"
            onChange={handleFileSelect}
          />
          
          {!selectedFile ? (
            <label htmlFor="resume-upload" className="cursor-pointer">
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">
                点击或拖拽上传简历
              </p>
              <p className="text-sm text-gray-500">
                支持 PDF、Word 格式，文件大小不超过 10MB
              </p>
            </label>
          ) : (
            <div className="flex items-center justify-center space-x-4">
              <File className="w-12 h-12 text-primary-600" />
              <div className="text-left">
                <p className="font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-sm text-gray-500">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                className="p-2 hover:bg-gray-100 rounded-full"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex space-x-4 mt-6">
          <button
            onClick={() => navigate('/')}
            className="flex-1 btn-secondary"
          >
            返回修改
          </button>
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploadResume.isPending}
            className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploadResume.isPending ? (
              <span className="flex items-center justify-center space-x-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>上传中...</span>
              </span>
            ) : (
              '开始分析'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
