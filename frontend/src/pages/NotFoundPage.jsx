import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <div className="mx-auto grid min-h-[70vh] max-w-3xl place-items-center px-6 text-center">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-moss">404</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight text-ink">Page not found</h1>
        <p className="mt-3 text-ink/55">This workspace route does not exist yet.</p>
        <Link to="/" className="mt-7 inline-flex rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-moss">
          Return to dashboard
        </Link>
      </div>
    </div>
  )
}

export default NotFoundPage

