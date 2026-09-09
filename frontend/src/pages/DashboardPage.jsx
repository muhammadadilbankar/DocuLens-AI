import { Link } from 'react-router-dom'

import HealthStatus from '../components/HealthStatus.jsx'
import { useHealth } from '../hooks/useHealth.js'

const pipeline = [
  ['01', 'Read', 'Scanned pages'],
  ['02', 'Understand', 'Local AI models'],
  ['03', 'Verify', 'Source highlights'],
]

function DashboardPage() {
  const { state, health, checkHealth } = useHealth()

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-16">
      <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="flex min-h-[31rem] flex-col justify-between rounded-[2rem] bg-ink p-7 text-white shadow-lift sm:p-10 lg:p-12">
          <div>
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-semibold text-white/70">
              <span className="h-1.5 w-1.5 rounded-full bg-lime" />
              Offline document intelligence
            </div>
            <h1 className="max-w-3xl text-4xl font-semibold leading-[1.05] tracking-[-0.04em] sm:text-6xl">
              Turn scanned pages into{' '}
              <span className="text-lime">evidence you can trace.</span>
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-white/60 sm:text-lg">
              Extract text, entities, and financial details locally—then jump back to the exact page and region they came from.
            </p>
          </div>

          <HealthStatus state={state} health={health} onRetry={checkHealth} />
        </div>

        <div className="grid gap-6">
          <article className="rounded-[2rem] border border-ink/10 bg-white/65 p-7 shadow-lift backdrop-blur sm:p-9">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-moss/65">Workspace</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">No documents yet</h2>
              </div>
              <span className="rounded-full bg-ink/5 px-3 py-1 text-xs font-semibold text-ink/50">Phase 2</span>
            </div>
            <div className="my-8 grid place-items-center rounded-2xl border border-dashed border-ink/15 bg-parchment/70 px-6 py-12 text-center">
              <div className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-white text-moss shadow-sm">
                <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" aria-hidden="true">
                  <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14.5v4.25C5 19.44 5.56 20 6.25 20h11.5c.69 0 1.25-.56 1.25-1.25V14.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <p className="font-semibold text-ink">Start with a scanned PDF</p>
              <p className="mt-1 max-w-xs text-sm leading-6 text-ink/50">Upload a document securely. Processing will be added in the next phases.</p>
              <Link to="/upload" className="mt-5 rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-moss">
                Upload PDF
              </Link>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-ink/45">Local processing</span>
              <span className="font-semibold text-moss">No cloud inference</span>
            </div>
          </article>

          <article className="rounded-[2rem] border border-ink/10 bg-lime/55 p-7 sm:p-8">
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-ink/50">Processing path</p>
            <div className="mt-5 grid grid-cols-3 gap-3">
              {pipeline.map(([number, title, subtitle]) => (
                <div key={number}>
                  <span className="text-xs font-bold text-moss/60">{number}</span>
                  <p className="mt-2 text-sm font-bold text-ink">{title}</p>
                  <p className="mt-0.5 text-xs text-ink/50">{subtitle}</p>
                </div>
              ))}
            </div>
          </article>
        </div>
      </section>

      <footer className="flex flex-col gap-2 px-2 pb-2 pt-8 text-xs text-ink/40 sm:flex-row sm:items-center sm:justify-between">
        <span>Built for the ARCIL document intelligence assignment</span>
        <span>Documents stay on this machine</span>
      </footer>
    </div>
  )
}

export default DashboardPage
