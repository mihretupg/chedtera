import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { API_BASE } from '../lib'

export default function ListingsFeedPage() {
  const [listings, setListings] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    fetch(`${API_BASE}/listings`)
      .then(async (res) => {
        if (!res.ok) throw new Error('Could not load listings')
        return res.json()
      })
      .then(setListings)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <section>
      <h2 className="mb-4 text-xl font-semibold">Listings Feed</h2>
      {error ? <p className="text-red-600">{error}</p> : null}
      <div className="grid gap-4 sm:grid-cols-2">
        {listings.map((listing) => (
          <article key={listing.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold">{listing.title}</h3>
            <p className="text-sm text-slate-600">{listing.category} • {listing.subcity}</p>
            <p className="mt-2 text-brand-700">{listing.price_birr} birr</p>
            <Link className="mt-3 inline-block text-sm font-semibold text-brand-700 hover:underline" to={`/listings/${listing.id}`}>
              View details
            </Link>
          </article>
        ))}
      </div>
      {!error && listings.length === 0 ? <p className="mt-3 text-slate-600">No published listings yet.</p> : null}
    </section>
  )
}
