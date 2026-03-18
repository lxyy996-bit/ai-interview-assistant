import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import UploadPage from './pages/UploadPage'
import AnalysisPage from './pages/AnalysisPage'
import ResultPage from './pages/ResultPage'

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/upload/:sessionId" element={<UploadPage />} />
          <Route path="/analysis/:sessionId" element={<AnalysisPage />} />
          <Route path="/result/:sessionId" element={<ResultPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
