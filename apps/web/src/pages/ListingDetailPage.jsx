import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { API_BASE, authHeaders } from '../lib'

export default function ListingDetailPage() {
  const { id } = useParams()
  const [listing, setListing] = useState(null)
  const [phone, setPhone] = useState('')
  const [chatAllowed, setChatAllowed] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/listings/${id}`)
      .then(async (res) => {
        if (!res.ok) throw new Error('Listing not found')
        return res.json()
      })
      .then(setListing)
      .catch((err) => setError(err.message))
  }, [id])

  async function unlockContact() {
    setError('')
    const res = await fetch(`${API_BASE}/listings/${id}/unlock`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
      },
    })

    const payload = await res.json()
    if (!res.ok) {
      setError(payload.detail || 'Unlock failed')
      return
    }

    setPhone(payload.seller_phone)
    setChatAllowed(payload.chat_allowed)
  }

  if (error) return <p className="text-red-600">{error}</p>
  if (!listing) return <p>Loading...</p>

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-2xl font-semibold">{listing.title}</h2>
      <p className="mt-1 text-sm text-slate-600">{listing.category} • {listing.subcity}</p>
      <p className="mt-2 text-brand-700">{listing.price_birr} birr</p>
      <p className="mt-4 text-slate-700">{listing.description}</p>

      <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <p className="text-sm text-slate-600">Seller phone is hidden until unlock.</p>
        {!phone ? (
          <button className="mt-3 rounded bg-brand-500 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700" onClick={unlockContact}>
            Unlock Contact
          </button>
        ) : (
          <div className="mt-3 space-y-1 text-sm">
            <p><span className="font-semibold">Seller phone:</span> {phone}</p>
            <p><span className="font-semibold">Chat allowed:</span> {chatAllowed ? 'Yes' : 'No'}</p>
          </div>
        )}
      </div>
    </section>
  )
}
