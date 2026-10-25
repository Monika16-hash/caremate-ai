import { useEffect, useState } from 'react'; import { api } from '../api'
export default function Doctor() {
  const [appts, setAppts] = useState(null)
  const load = () => api('/appointments').then(setAppts)
  useEffect(() => { load() }, [])
  const act = (id, status) => api(`/appointments/${id}`, { method: 'PATCH', body: { status } }).then(load)
  return (
    <div className="rounded-2xl bg-white p-4 shadow dark:bg-slate-800">
      <h1 className="mb-2 font-semibold">Appointments</h1>
      {!appts ? <div className="skeleton h-12" /> : appts.length === 0 ? <p className="text-slate-500">No appointments yet.</p> : appts.map((a) => (
        <div key={a.id} className="flex flex-wrap items-center justify-between gap-2 border-t py-2 dark:border-slate-700">
          <span>{a.date} {a.slot} · {a.status} · no-show risk {Math.round(a.noshow_risk * 100)}%</span>
          <span className="flex gap-2">
            {a.status === 'pending' && <><button onClick={() => act(a.id, 'approved')} className="rounded bg-secondary px-3 text-white">Approve</button><button onClick={() => act(a.id, 'rejected')} className="rounded bg-red-600 px-3 text-white">Reject</button></>}
            {a.status === 'approved' && <><button onClick={() => act(a.id, 'completed')} className="rounded bg-primary px-3 text-white">Attended</button><button onClick={() => act(a.id, 'missed')} className="rounded bg-slate-600 px-3 text-white">No-show</button></>}
          </span></div>))}
    </div>
  )
}
