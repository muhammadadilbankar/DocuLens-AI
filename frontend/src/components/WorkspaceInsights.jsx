import { useState } from 'react'

import EntityPanel from './EntityPanel.jsx'

const tabs = [
  { id: 'text', label: 'OCR text' },
  { id: 'entities', label: 'Entities' },
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

function WorkspaceInsights({ document, page, entities, onEntitySelect, selectedEntityId }) {
  const [activeTab, setActiveTab] = useState('text')
  const [entityScope, setEntityScope] = useState('page')
  const pageEntities = page?.entities ?? []
  const visibleEntities = entityScope === 'page' ? pageEntities : entities
  const confidence = page?.average_ocr_confidence

  return (
    <aside className="min-w-0 overflow-hidden rounded-[1.5rem] border border-ink/10 bg-white/75 shadow-sm backdrop-blur">
      <div className="border-b border-ink/10 px-3 pt-3">
        <div className="grid grid-cols-3 gap-1 rounded-xl bg-ink/5 p-1" role="tablist" aria-label="Document insights">
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

        {activeTab === 'details' ? (
          <dl>
            <DetailRow label="File name" value={document?.original_filename ?? '—'} />
            <DetailRow label="Document ID" value={document?.id ?? '—'} mono />
            <DetailRow label="Processing status" value={document?.status?.replaceAll('_', ' ') ?? '—'} />
            <DetailRow label="Created" value={document?.created_at ? new Date(document.created_at).toLocaleString() : '—'} />
            <DetailRow label="Page dimensions" value={page ? `${page.image_width} × ${page.image_height} px` : '—'} />
            <DetailRow label="OCR regions" value={page?.ocr_blocks?.length ?? 0} />
            <DetailRow label="Page entities" value={pageEntities.length} />
          </dl>
        ) : null}
      </div>
    </aside>
  )
}

export default WorkspaceInsights
