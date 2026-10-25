import { useEffect, useState } from 'react'
import { api } from '../api'; import { Toast } from '../Toast'
import SmartToyIcon from '@mui/icons-material/SmartToy'; import EventIcon from '@mui/icons-material/Event'
const card = 'rounded-2xl bg-white p-4 shadow dark:bg-slate-800'
const field = 'rounded-lg border border-slate-300 p-2 dark:border-slate-600 dark:bg-slate-800'

export default function Patient() {
  const [appts, setAppts] = useState(null); const [docs, setDocs] = useState([]); const [filters, setFilters] = useState({ q: '', specialty: '', location: '', hospital: '' })
  const [msg, setMsg] = useState(''); const [ai, setAi] = useState(null); const [text, setText] = useState(''); const [slot, setSlot] = useState({ date: '', time: '' }); const [report, setReport] = useState(null)
  const [checking, setChecking] = useState(false); const [aiError, setAiError] = useState('')
  const toast = (m) => { setMsg(m); setTimeout(() => setMsg(''), 3000) }
  const loadAppts = () => api('/appointments').then(setAppts).catch((e) => toast(e.message))
const search = async (f = filters) => {
  setSearching(true); setSearchError('')
  try {
    const r = await api('/doctors?' + new URLSearchParams(f))
    setDocs(Array.isArray(r) ? r : [])
  } catch (e) { setDocs([]); setSearchError(e.message) } finally { setSearching(false) }
}  
const [searching, setSearching] = useState(false); const [searchError, setSearchError] = useState('')
  useEffect(() => { loadAppts(); search() }, [])

  
  async function check() {
  if (!text.trim()) return
  setChecking(true); setAiError(''); setAi(null)
  try {
    const r = await api('/ai/symptoms', { method: 'POST', body: { message: text } })
    setAi(r)
    const f = { q: '', location: '', hospital: '', specialty: r.specialty || '' }
    setFilters(f); search(f)
  } catch (e) { setAiError(e.message) } finally { setChecking(false) }
}
  async function book(id) {
    try { await api('/appointments', { method: 'POST', body: { doctor_id: id, date: slot.date, slot: slot.time } }); toast('Appointment requested. Check your email.'); loadAppts() } catch (e) { toast(e.message) }
  }
  async function upload(e) {
    const form = new FormData(); form.append('file', e.target.files[0])
    try { setReport(await api('/reports', { method: 'POST', form })) } catch (err) { toast(err.message) }
  }
  const today = new Date().toISOString().slice(0, 10)
  const upcoming = (appts || []).filter((a) => a.date >= today), past = (appts || []).filter((a) => a.date < today)
  return (
    <div className="space-y-4">
      <section className={card}><h2 className="mb-2 flex items-center gap-2 font-semibold"><SmartToyIcon className="text-secondary" />Describe your symptoms</h2>
        <div className="flex gap-2"><input className={field + ' flex-1'} value={text} onChange={(e) => setText(e.target.value)} placeholder="I have chest pain and dizziness" /><button onClick={check} className="rounded-lg bg-secondary px-4 text-white">Check</button></div>
        {ai && <p className="mt-2">Suggested specialist: <b>{ai.specialty}</b>. {ai.reason}</p>}
        <p className="mt-1 text-xs text-slate-500">AI recommendation only. Not a medical diagnosis.</p></section>
      <section className={card}><h2 className="mb-2 flex items-center gap-2 font-semibold"><EventIcon className="text-primary" />Appointments</h2>
        {!appts ? <div className="skeleton h-12" /> : upcoming.length ? upcoming.map((a) => <p key={a.id}>{a.date} {a.slot} · {a.status}</p>) : <p className="text-slate-500">Nothing booked. Find a doctor below.</p>}
        {past.length > 0 && <p className="mt-2 text-sm text-slate-500">{past.length} previous appointment(s)</p>}</section>
      <section className={card}><h2 className="mb-2 font-semibold">Find a doctor</h2>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{Object.keys(filters).map((k) => <input key={k} className={field} placeholder={k === 'q' ? 'Name' : k} value={filters[k]} onChange={(e) => setFilters({ ...filters, [k]: e.target.value })} />)}</div>
        <button onClick={check} disabled={checking} className="rounded-lg bg-secondary px-4 text-white disabled:opacity-50">{checking ? 'Checking…' : 'Check'}</button>
...
{aiError && <p role="alert" className="mt-2 text-red-600">{aiError}</p>}
{ai && (
  <div className="mt-2 rounded-lg bg-teal-50 p-3 dark:bg-slate-700">
    <p>Suggested specialist: <b>{ai.specialty}</b></p>
    {ai.reason && <p className="text-sm">{ai.reason}</p>}
    {ai.urgent && <p className="text-sm font-medium text-red-600">These symptoms may need urgent care. Contact emergency services or visit a hospital now.</p>}
    {ai.source === 'keywords' && <p className="text-xs text-slate-500">AI service unavailable, so this is a basic keyword match.</p>}
  </div>
)}
        <div className="mt-2 flex gap-2"><input type="date" min={today} className={field} onChange={(e) => setSlot({ ...slot, date: e.target.value })} />
          <select className={field} onChange={(e) => setSlot({ ...slot, time: e.target.value })}><option value="">Time slot</option>{['09:00', '10:00', '11:00', '14:00', '15:00'].map((t) => <option key={t}>{t}</option>)}</select></div>
        {docs.map((d) => <div key={d.id} className="mt-2 flex items-center justify-between border-t pt-2 dark:border-slate-700"><span><b>{d.name}</b> · {d.specialization} · {d.hospital}, {d.location}</span>
          <button disabled={!slot.date || !slot.time} onClick={() => book(d.id)} className="rounded-lg bg-primary px-3 py-1 text-white disabled:opacity-40">Book</button></div>)}</section>
      <section className={card}><h2 className="mb-2 font-semibold">Analyze a medical report</h2><input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={upload} />
        {report && <div className="mt-2 text-sm">{Object.entries(report).map(([k, v]) => <div key={k}><b>{k.replace('_', ' ')}</b><ul className="list-disc pl-5">{v.map((i, n) => <li key={n}>{i}</li>)}</ul></div>)}</div>}</section>
      <Toast msg={msg} />
    </div>
  )
}
