import { useEffect, useState } from 'react'; import { api } from '../api'
const Bars = ({ title, data }) => { const max = Math.max(1, ...Object.values(data)); return (
  <div className="rounded-2xl bg-white p-4 shadow dark:bg-slate-800"><h2 className="mb-2 font-semibold">{title}</h2>
    {Object.entries(data).map(([k, v]) => <div key={k} className="mb-1 flex items-center gap-2 text-sm"><span className="w-28 truncate">{k}</span><div className="h-3 rounded bg-primary" style={{ width: `${(v / max) * 100}%` }} /><span>{v}</span></div>)}</div>) }
export default function Admin() {
  const [d, setD] = useState(null)
  useEffect(() => { api('/admin/analytics').then(setD) }, [])
  if (!d) return <div className="skeleton h-32" />
  return (
    <div className="space-y-4">
      <p>Patients {d.totals.patients} · Doctors {d.totals.doctors} · Appointments {d.totals.appointments} · No-show rate {(d.no_show_rate * 100).toFixed(1)}%</p>
      <Bars title="Appointments per day" data={d.appointments_per_day} /><Bars title="Most searched specialization" data={d.top_specializations} />
    </div>
  )
}
