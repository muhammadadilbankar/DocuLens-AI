import { useEffect, useState } from 'react'

import EntityPanel from './EntityPanel.jsx'
import { getApiErrorMessage, searchDocument } from '../services/api.js'

const tabs = [
  { id: 'text', label: 'OCR text' },
  { id: 'entities', label: 'Entities' },
  { id: 'search', label: 'Search' },
  { id: 'details', label: 'Details' },
]

function DetailRow({ label, value, mono = false }) {
  return (
    <div className="border-b border-ink/10 py-3 last:border-0">
      <dt className="text-[10px] font-bold uppercase tracking-[0.14em] text-ink/35">{label}</dt>
      <dd className={`mt-1 break-words text-sm font-semibold text-ink ${mono ? 'font-mono text-xs' : ''}`}>{value}</dd>
    </div>
  )
}

function WorkspaceInsights({ document, page, entities, onEntitySelect, selectedEntityId, onSearchResultSelect }) {
  const [activeTab, setActiveTab] = useState('text')
  const [entityScope, setEntityScope] = useState('page')
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [lastSearchQuery, setLastSearchQuery] = useState('')
  const pageEntities = page?.entities ?? []
  const visibleEntities = entityScope === 'page' ? pageEntities : entities
  const confidence = page?.average_ocr_confidence
  const searchReady = document?.status === 'COMPLETED' && document.indexed_chunk_count > 0

  useEffect(() => {
    setQuery('')
    setSearchResults([])
    setSearchError('')
    setLastSearchQuery('')
  }, [document?.id])

  const submitSearch = async (event) => {
    event.preventDefault()
    const normalizedQuery = query.trim()
    if (normalizedQuery.length < 2) return
    setSearching(true)
    setSearchError('')
    setSearchResults([])
    try {
      const response = await searchDocument(document.id, normalizedQuery)
      setSearchResults(response.results)
      setLastSearchQuery(response.query)
    } catch (requestError) {
      setSearchResults([])
      setLastSearchQuery('')
      setSearchError(getApiErrorMessage(requestError))
    } finally {
      setSearching(false)
    }
  }

  return (
    <aside className="min-w-0 overflow-hidden rounded-[1.5rem] border border-ink/10 bg-white/75 shadow-sm backdrop-blur">
      <div className="border-b border-ink/10 px-3 pt-3">
        <div className="grid grid-cols-4 gap-1 rounded-xl bg-ink/5 p-1" role="tablist" aria-label="Document insights">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg px-2 py-2 text-[10px] font-bold transition ${activeTab === tab.id ? 'bg-white text-ink shadow-sm' : 'text-ink/45 hover:text-ink'}`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="flex items-center justify-between px-2 py-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-moss/60">Page {page?.page_number ?? '—'}</p>
            <h2 className="mt-0.5 text-lg font-semibold text-ink">{tabs.find((tab) => tab.id === activeTab)?.label}</h2>
          </div>
          {confidence !== null && confidence !== undefined ? (
            <div className="text-right">
              <p className="text-lg font-bold text-ink">{Math.round(confidence * 100)}%</p>
              <p className="text-[9px] font-bold uppercase tracking-wide text-ink/35">OCR confidence</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="max-h-[calc(100vh-18rem)] min-h-[32rem] overflow-y-auto p-4 lg:min-h-[38rem]">
        {activeTab === 'text' ? (
          page?.ocr_completed ? (
            <div>
              <div className="rounded-xl border border-ink/10 bg-parchment/45 p-4">
                <p className="whitespace-pre-wrap text-sm leading-7 text-ink/80">{page.cleaned_text || 'No readable text was detected.'}</p>
              </div>
              {page.ocr_blocks?.length ? (
                <div className="mt-5">
                  <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.16em] text-ink/35">OCR regions</p>
                  <div className="space-y-2">
                    {page.ocr_blocks.map((block) => (
                      <div key={block.id} className="flex items-start justify-between gap-3 rounded-lg border border-ink/10 px-3 py-2.5">
                        <p className="text-xs leading-5 text-ink/70">{block.text}</p>
                        <span className="shrink-0 text-[9px] font-bold text-moss">{Math.round(block.confidence * 100)}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="rounded-xl bg-ink/5 p-4 text-sm leading-6 text-ink/45">OCR has not processed this page yet.</p>
          )
        ) : null}

        {activeTab === 'entities' ? (
          <div>
            <div className="mb-3 flex rounded-full bg-ink/5 p-1">
              {[
                { id: 'page', label: `This page (${pageEntities.length})` },
                { id: 'document', label: `Document (${entities.length})` },
              ].map((scope) => (
                <button key={scope.id} type="button" aria-pressed={entityScope === scope.id} onClick={() => setEntityScope(scope.id)} className={`flex-1 rounded-full px-2 py-1.5 text-[10px] font-bold transition ${entityScope === scope.id ? 'bg-white text-ink shadow-sm' : 'text-ink/45'}`}>{scope.label}</button>
              ))}
            </div>
            <p className="mb-3 text-[10px] leading-4 text-ink/40">Select an entity to reveal its source region on the enhanced page.</p>
            <EntityPanel
              entities={visibleEntities}
              showPage={entityScope === 'document'}
              compact
              onEntitySelect={onEntitySelect}
              selectedEntityId={selectedEntityId}
            />
          </div>
        ) : null}

        {activeTab === 'search' ? (
          <div>
            <form onSubmit={submitSearch}>
              <label htmlFor="document-search" className="text-[10px] font-bold uppercase tracking-[0.14em] text-ink/40">Ask about this document</label>
              <div className="mt-2 flex gap-2">
                <input
                  id="document-search"
                  type="search"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="What is the loan amount?"
                  minLength={2}
                  maxLength={500}
                  className="min-w-0 flex-1 rounded-xl border border-ink/10 bg-white px-3 py-2.5 text-sm text-ink outline-none transition placeholder:text-ink/30 focus:border-moss focus:ring-2 focus:ring-lime/30"
                />
                <button type="submit" disabled={searching || query.trim().length < 2 || !searchReady} className="rounded-xl bg-ink px-4 py-2.5 text-xs font-bold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-40">{searching ? 'Searching…' : 'Search'}</button>
              </div>
            </form>
            {!searchReady ? <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-800">Semantic search becomes available after the local search index is built.</p> : null}
            {searchError ? <p role="alert" className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs leading-5 text-rose-700">{searchError}</p> : null}
            {searchResults.length ? (
              <div className="mt-4 space-y-3" aria-live="polite" aria-label={`Results for ${lastSearchQuery}`}>
                {searchResults.map((result, index) => (
                  <button key={result.chunk_id} type="button" onClick={() => onSearchResultSelect(result)} aria-label={`Open result ${index + 1} on page ${result.page_number}`} className="w-full rounded-xl border border-ink/10 bg-parchment/45 p-3 text-left transition hover:border-moss/40 hover:bg-lime/10">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-[10px] font-bold uppercase tracking-wide text-moss">#{index + 1} · Page {result.page_number}</span>
                      <span className="text-[10px] font-bold text-ink/40">{Math.round(result.score * 100)}% match</span>
                    </div>
                    <p className="mt-2 line-clamp-5 text-xs leading-5 text-ink/70">{result.content}</p>
                  </button>
                ))}
              </div>
            ) : !searching && lastSearchQuery && !searchError ? <p className="mt-4 text-xs leading-5 text-ink/40">No matching passages were found.</p> : null}
          </div>
        ) : null}

        {activeTab === 'details' ? (
          <dl>
            <DetailRow label="File name" value={document?.original_filename ?? '—'} />
            <DetailRow label="Document ID" value={document?.id ?? '—'} mono />
            <DetailRow label="Processing status" value={document?.status?.replaceAll('_', ' ') ?? '—'} />
            <DetailRow label="Created" value={document?.created_at ? new Date(document.created_at).toLocaleString() : '—'} />
            <DetailRow label="Page dimensions" value={page ? `${page.image_width} × ${page.image_height} px` : '—'} />
            <DetailRow label="OCR regions" value={page?.ocr_blocks?.length ?? 0} />
            <DetailRow label="Page entities" value={pageEntities.length} />
            <DetailRow label="Indexed chunks" value={document?.indexed_chunk_count ?? 0} />
          </dl>
        ) : null}
      </div>
    </aside>
  )
}

export default WorkspaceInsights
