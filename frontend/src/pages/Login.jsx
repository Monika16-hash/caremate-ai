import { useState } from 'react'; import { useNavigate } from 'react-router-dom'
import { api, session } from '../api'
const field = 'w-full rounded-lg border border-slate-300 p-2 dark:border-slate-600 dark:bg-slate-800'
export default function Login() {
  const [f, setF] = useState({ role: 'patient', mode: 'login', name: '', email: '', password: '', specialization: '', hospital: '', location: '' })
  const [error, setError] = useState(''); const nav = useNavigate()
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  async function submit(e) {
    e.preventDefault(); setError('')
    try {
      const r = await api(f.mode === 'login'? '/api/auth/login': '/api/auth/register',{ method: 'POST', body: f })
      session.set({ token: r.token, role: r.role }); nav(`/${r.role}`)
    } catch (err) { setError(err.message) }
  }
  return (
    <form onSubmit={submit} className="mx-auto mt-8 max-w-sm space-y-3 rounded-2xl bg-white p-6 shadow dark:bg-slate-800">
      <h1 className="text-xl font-semibold">{f.mode === 'login' ? 'Log in' : 'Create account'}</h1>
      <select className={field} value={f.role} onChange={set('role')}><option value="patient">Patient</option><option value="doctor">Doctor</option><option value="admin">Admin</option></select>
      {f.mode === 'register' && <input className={field} placeholder="Full name" value={f.name} onChange={set('name')} required />}
      {f.mode === 'register' && f.role === 'doctor' && ['specialization', 'hospital', 'location'].map((k) => <input key={k} className={field} placeholder={k[0].toUpperCase() + k.slice(1)} value={f[k]} onChange={set(k)} required />)}
      <input className={field} type="email" placeholder="Email" value={f.email} onChange={set('email')} required />
      <input className={field} type="password" placeholder="Password (8+ characters)" value={f.password} onChange={set('password')} required minLength={8} />
      {error && <p role="alert" className="text-sm text-red-600">{error}</p>}
      <button className="w-full rounded-lg bg-primary p-2 font-medium text-white">{f.mode === 'login' ? 'Log in' : 'Sign up'}</button>
      {f.role !== 'admin' && <button type="button" className="text-sm text-secondary" onClick={() => setF({ ...f, mode: f.mode === 'login' ? 'register' : 'login' })}>{f.mode === 'login' ? 'New here? Create an account' : 'Have an account? Log in'}</button>}
    </form>
  )
}
