import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import DigestDetail from './pages/DigestDetail'
import Channels from './pages/Channels'
import History from './pages/History'
import Settings from './pages/Settings'
import Toast from './components/Toast'
import { useState, useCallback } from 'react'

export default function App() {
  const [toast, setToast] = useState(null)

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  return (
    <div className="app">
      <Sidebar />
      <div className="app-content">
        <header className="app-header">
          <h1>📧 Email Digest Summarizer</h1>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Dashboard showToast={showToast} />} />
            <Route path="/digest/:id" element={<DigestDetail showToast={showToast} />} />
            <Route path="/channels" element={<Channels showToast={showToast} />} />
            <Route path="/history" element={<History showToast={showToast} />} />
            <Route path="/settings" element={<Settings showToast={showToast} />} />
          </Routes>
        </main>
      </div>
      {toast && <Toast message={toast.message} type={toast.type} />}
    </div>
  )
}
