import { Route, Routes } from 'react-router-dom'

import AppShell from './components/AppShell.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import DocumentUploadedPage from './pages/DocumentUploadedPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import UploadPage from './pages/UploadPage.jsx'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/documents/:id" element={<DocumentUploadedPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AppShell>
  )
}

export default App
