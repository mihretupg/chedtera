import { useState } from 'react'
import { saveUser } from '../lib'

export default function LoginPage() {
  const [id, setId] = useState('')
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [role, setRole] = useState('buyer')
  const [message, setMessage] = useState('')

  function onSubmit(e) {
    e.preventDefault()
    if (!id || !name || !phone) {
      setMessage('All fields are required.')
      return
    }

    saveUser({ id: Number(id), name, phone, role })
    setMessage('Saved. You can now browse listings and unlock contacts.')
  }

  return (
    <section className="mx-auto max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">Login</h2>
      <form className="space-y-3" onSubmit={onSubmit}>
        <input className="w-full rounded border border-slate-300 px-3 py-2" placeholder="User ID" value={id} onChange={(e) => setId(e.target.value)} />
        <input className="w-full rounded border border-slate-300 px-3 py-2" placeholder="Full name" value={name} onChange={(e) => setName(e.target.value)} />
        <input className="w-full rounded border border-slate-300 px-3 py-2" placeholder="Phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
        <select className="w-full rounded border border-slate-300 px-3 py-2" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="buyer">Buyer</option>
          <option value="seller">Seller</option>
        </select>
        <button className="w-full rounded bg-brand-500 px-4 py-2 font-semibold text-white hover:bg-brand-700" type="submit">
          Save Session
        </button>
      </form>
      {message ? <p className="mt-4 text-sm text-slate-600">{message}</p> : null}
    </section>
  )
}
