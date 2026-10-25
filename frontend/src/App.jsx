import { useEffect, useState } from 'react'
import { Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom'
import DarkModeIcon from '@mui/icons-material/DarkMode'; import LightModeIcon from '@mui/icons-material/LightMode'
import LogoutIcon from '@mui/icons-material/Logout'
import { session } from './api'
import Login from './pages/Login'; import Patient from './pages/Patient'; import Doctor from './pages/Doctor'; import Admin from './pages/Admin'

function Guard({ role, children }) {
  const s = session.get()
  return s && s.role === role ? children : <Navigate to="/login" replace />
}

export default function App() {
  const [dark, setDark] = useState(localStorage.getItem('cm_dark') === '1')
  const nav = useNavigate(); const s = session.get()
  useEffect(() => { document.documentElement.classList.toggle('dark', dark); localStorage.setItem('cm_dark', dark ? '1' : '0') }, [dark])
  return (
    <div className="min-h-screen text-slate-800 dark:text-slate-100">
      <header className="flex items-center justify-between bg-primary px-4 py-3 text-white">
        <Link to="/" className="text-lg font-semibold">CareMate AI</Link>
        <div className="flex gap-3">
          <button aria-label="Toggle theme" onClick={() => setDark(!dark)}>{dark ? <LightModeIcon /> : <DarkModeIcon />}</button>
          {s && <button aria-label="Log out" onClick={() => { session.clear(); nav('/login') }}><LogoutIcon /></button>}
        </div>
      </header>
      <main className="mx-auto max-w-4xl p-4">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/patient" element={<Guard role="patient"><Patient /></Guard>} />
          <Route path="/doctor" element={<Guard role="doctor"><Doctor /></Guard>} />
          <Route path="/admin" element={<Guard role="admin"><Admin /></Guard>} />
          <Route path="*" element={<Navigate to={s ? `/${s.role}` : '/login'} replace />} />
        </Routes>
      </main>
    </div>
  )
}
