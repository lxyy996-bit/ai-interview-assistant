import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import UploadPage from './pages/UploadPage'
import AnalysisPage from './pages/AnalysisPage'
import ResultPage from './pages/ResultPage'
import LoginPage from './pages/LoginPage'
import AdminLoginPage from './pages/AdminLoginPage'
import AdminDashboard from './pages/AdminDashboard'

// 用户路由保护
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token')
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

// 管理员路由保护
function AdminRoute({ children }: { children: React.ReactNode }) {
  const adminToken = localStorage.getItem('admin_token')
  if (!adminToken) {
    return <Navigate to="/admin/login" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 用户登录 */}
        <Route path="/login" element={<LoginPage />} />
        
        {/* 管理员登录 */}
        <Route path="/admin/login" element={<AdminLoginPage />} />
        
        {/* 管理员后台 */}
        <Route path="/admin" element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        } />
        
        {/* 用户页面（需要登录） */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout>
              <HomePage />
            </Layout>
          </ProtectedRoute>
        } />
        <Route path="/upload/:sessionId" element={
          <ProtectedRoute>
            <Layout>
              <UploadPage />
            </Layout>
          </ProtectedRoute>
        } />
        <Route path="/analysis/:sessionId" element={
          <ProtectedRoute>
            <Layout>
              <AnalysisPage />
            </Layout>
          </ProtectedRoute>
        } />
        <Route path="/result/:sessionId" element={
          <ProtectedRoute>
            <Layout>
              <ResultPage />
            </Layout>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  )
}

export default App
