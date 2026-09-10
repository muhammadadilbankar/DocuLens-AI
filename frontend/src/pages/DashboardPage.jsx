import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import DocumentStatusBadge from '../components/DocumentStatusBadge.jsx'
import HealthStatus from '../components/HealthStatus.jsx'
import { useDocuments } from '../hooks/useDocuments.js'
import { useHealth } from '../hooks/useHealth.js'

const pipeline = [
  ['01', 'Read', 'Scanned pages'],
  ['02', 'Understand', 'Local AI models'],
  ['03', 'Verify', 'Source highlights'],
]

const activeStatuses = new Set(['CONVERTING', 'PREPROCESSING', 'OCR_PROCESSING', 'EXTRACTING_ENTITIES', 'INDEXING'])

function DashboardPage() {
  const { state, health, checkHealth } = useHealth()
  const location = useLocation()
  const { documents, loading, deletingId, error, refresh, remove } = useDocuments()
  const [notice, setNotice] = useState(location.state?.notice ?? '')

  const deleteFromHistory = async (document) => {
    const confirmed = window.confirm(
      `Permanently delete “${document.original_filename}” and all of its extracted data and local files?`,
    )
    if (!confirmed) return

    const result = await remove(document.id)
    if (result) {
      setNotice(
        result.cleanup_warnings.length
          ? `Document deleted. ${result.cleanup_warnings.join(' ')}`
          : 'Document and its local files were deleted.',
      )
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-16">
      {notice ? <p role="status" className="mb-5 rounded-2xl border border-moss/15 bg-lime/30 px-5 py-3 text-sm font-semibold text-ink">{notice}</p> : null}
      {error ? <div role="alert" className="mb-5 flex items-center justify-between gap-4 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-3 text-sm text-rose-700"><span>{error}</span><button type="button" onClick={refresh} className="shrink-0 font-bold underline">Retry</button></div> : null}
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
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-ink">Document history</h2>
              </div>
              <span className="rounded-full bg-ink/5 px-3 py-1 text-xs font-semibold text-ink/50">{documents.length} retained</span>
            </div>
            <div className="my-6 max-h-[28rem] space-y-2 overflow-y-auto pr-1">
              {loading ? <p className="rounded-2xl bg-parchment/70 px-5 py-10 text-center text-sm font-semibold text-ink/45">Loading document history…</p> : null}
              {!loading && !documents.length ? (
                <div className="grid place-items-center rounded-2xl border border-dashed border-ink/15 bg-parchment/70 px-6 py-10 text-center">
                  <p className="font-semibold text-ink">No retained documents</p>
                  <p className="mt-1 text-sm leading-6 text-ink/50">Upload a scanned PDF to begin.</p>
                </div>
              ) : null}
              {documents.map((document) => {
                const processing = activeStatuses.has(document.status)
                const deleting = deletingId === document.id
                return (
                  <article key={document.id} className="rounded-2xl border border-ink/10 bg-parchment/55 p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-ink" title={document.original_filename}>{document.original_filename}</p>
                        <p className="mt-1 text-[10px] text-ink/40">{new Date(document.created_at).toLocaleString()}</p>
                      </div>
                      <DocumentStatusBadge status={document.status} />
                    </div>
                    <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                      <p className="text-[10px] font-semibold text-ink/45">{document.page_count} pages · {document.entity_count} entities · {document.indexed_chunk_count} chunks</p>
                      <div className="flex gap-2">
                        <Link to={`/documents/${document.id}`} className="rounded-full bg-ink px-3 py-1.5 text-[10px] font-bold text-white transition hover:bg-moss">Open</Link>
                        <button type="button" onClick={() => deleteFromHistory(document)} disabled={processing || deleting} title={processing ? 'Wait for processing to finish' : 'Permanently delete document'} className="rounded-full border border-rose-200 px-3 py-1.5 text-[10px] font-bold text-rose-700 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-35">{deleting ? 'Deleting…' : 'Delete'}</button>
                      </div>
                    </div>
                  </article>
                )
              })}
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-ink/45">Local processing</span>
              <Link to="/upload" className="rounded-full bg-ink px-4 py-2 text-xs font-bold text-white transition hover:bg-moss">Upload PDF</Link>
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
