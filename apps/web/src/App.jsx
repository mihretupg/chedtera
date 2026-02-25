import { Link, Route, Routes } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import ListingsFeedPage from './pages/ListingsFeedPage'
import ListingDetailPage from './pages/ListingDetailPage'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold text-brand-700">Chedtera</h1>
          <nav className="flex gap-4 text-sm font-medium text-slate-700">
            <Link to="/login" className="hover:text-brand-700">Login</Link>
            <Link to="/" className="hover:text-brand-700">Listings</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/listings/:id" element={<ListingDetailPage />} />
          <Route path="/" element={<ListingsFeedPage />} />
        </Routes>
      </main>
    </div>
  )
}
