import { Link, NavLink } from 'react-router-dom'

const navLinkClass = ({ isActive }) =>
  `rounded-full px-4 py-2 text-sm font-medium transition ${
    isActive
      ? 'bg-ink text-white'
      : 'text-ink/60 hover:bg-white/70 hover:text-ink'
  }`

function AppShell({ children }) {
  return (
    <div className="relative min-h-screen overflow-hidden bg-parchment">
      <div className="pointer-events-none absolute -right-36 -top-40 h-[34rem] w-[34rem] rounded-full bg-lime/35 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-64 -left-48 h-[38rem] w-[38rem] rounded-full bg-emerald-200/30 blur-3xl" />

      <header className="relative z-10 border-b border-ink/10 bg-parchment/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
          <Link to="/" className="group flex items-center gap-3" aria-label="DocuLens AI home">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-ink text-lime shadow-sm transition group-hover:-rotate-3">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden="true">
                <path d="M7 3.75h7l3 3V20.25H7V3.75Z" stroke="currentColor" strokeWidth="1.7" />
                <path d="M14 3.75v3h3M9.5 11h5M9.5 14.5h3.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
            </span>
            <span>
              <span className="block text-[15px] font-bold leading-tight tracking-tight">DocuLens AI</span>
              <span className="block text-[10px] font-semibold uppercase tracking-[0.2em] text-ink/45">Private by design</span>
            </span>
          </Link>

          <nav className="flex items-center gap-1" aria-label="Primary navigation">
            <NavLink to="/" className={navLinkClass}>Dashboard</NavLink>
            <span className="hidden rounded-full px-4 py-2 text-sm font-medium text-ink/30 sm:inline">Upload · Phase 2</span>
          </nav>
        </div>
      </header>

      <main className="relative z-10">{children}</main>
    </div>
  )
}

export default AppShell

