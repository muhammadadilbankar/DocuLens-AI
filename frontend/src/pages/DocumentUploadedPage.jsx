import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import DocumentStatusBadge from '../components/DocumentStatusBadge.jsx'
import WorkspaceDocumentViewer from '../components/WorkspaceDocumentViewer.jsx'
import WorkspaceInsights from '../components/WorkspaceInsights.jsx'
import WorkspacePageRail from '../components/WorkspacePageRail.jsx'
import { useDocumentPages } from '../hooks/useDocumentPages.js'
import { getApiErrorMessage, getDocumentPage } from '../services/api.js'

const activeStatuses = new Set(['CONVERTING', 'PREPROCESSING', 'OCR_PROCESSING', 'EXTRACTING_ENTITIES'])

function processingMessage(document) {
  if (document.status === 'CONVERTING') return 'Rendering document pages with PyMuPDF…'
  if (document.status === 'PREPROCESSING') return 'Improving scan quality with OpenCV…'
  if (document.status === 'OCR_PROCESSING') return `Reading pages with PaddleOCR… ${document.ocr_page_count}/${document.page_count}`
  return `Extracting entities with local NLP… ${document.entity_count} found`
}

function DocumentUploadedPage() {
  const { id } = useParams()
  const {
    document,
    pages,
    entities,
    loading,
    starting,
    pipelineRequested,
    error,
    refresh,
    startConversion,
  } = useDocumentPages(id)
  const [selectedPageNumber, setSelectedPageNumber] = useState(null)
  const [selectedPage, setSelectedPage] = useState(null)
  const [pageLoading, setPageLoading] = useState(false)
  const [pageError, setPageError] = useState('')
  const [variant, setVariant] = useState('preprocessed')
  const [showOverlays, setShowOverlays] = useState(true)
  const [highlightedEntity, setHighlightedEntity] = useState(null)

  useEffect(() => {
    if (pages.length && !pages.some((page) => page.page_number === selectedPageNumber)) {
      setSelectedPageNumber(pages[0].page_number)
    }
  }, [pages, selectedPageNumber])

  useEffect(() => {
    if (!selectedPageNumber) return undefined
    let isCurrent = true
    setSelectedPage((currentPage) => currentPage?.page_number === selectedPageNumber ? currentPage : null)
    setPageLoading(true)
    setPageError('')
    getDocumentPage(id, selectedPageNumber)
      .then((page) => {
        if (isCurrent) setSelectedPage(page)
      })
      .catch((requestError) => {
        if (isCurrent) setPageError(getApiErrorMessage(requestError))
      })
      .finally(() => {
        if (isCurrent) setPageLoading(false)
      })
    return () => {
      isCurrent = false
    }
  }, [document?.entity_count, document?.status, id, selectedPageNumber])

  const selectedIndex = pages.findIndex((page) => page.page_number === selectedPageNumber)
  const isLegacyPagesReady = document?.status === 'PREPROCESSING' && pages.length > 0 && !pipelineRequested && pages.every((page) => !page.preprocessed_image_url)
  const isReadyForOcr = document?.status === 'OCR_PROCESSING' && pages.length > 0 && !pipelineRequested && pages.some((page) => !page.ocr_completed)
  const isReadyForEntities = document?.status === 'EXTRACTING_ENTITIES' && !pipelineRequested
  const canStart = document?.status === 'UPLOADED' || document?.status === 'FAILED' || isLegacyPagesReady || isReadyForOcr || isReadyForEntities
  const isProcessing = Boolean(document && activeStatuses.has(document.status))
  const actionLabel = document?.status === 'FAILED'
    ? 'Retry processing'
    : isLegacyPagesReady
      ? 'Preprocess pages'
      : isReadyForOcr
        ? 'Run offline OCR'
        : isReadyForEntities
          ? 'Extract entities'
          : 'Process document'

  const selectPage = (pageNumber) => {
    setHighlightedEntity(null)
    setSelectedPageNumber(pageNumber)
  }

  const selectEntity = (entity) => {
    setHighlightedEntity(entity)
    setSelectedPageNumber(entity.page_number)
    setVariant('preprocessed')
    setShowOverlays(true)
  }

  if (loading) {
    return <div className="mx-auto max-w-7xl px-5 py-20 text-center text-sm font-semibold text-ink/50">Loading document…</div>
  }

  return (
    <div className="mx-auto max-w-[96rem] px-4 py-6 sm:px-6 lg:px-8">
      <header className="overflow-hidden rounded-[1.75rem] bg-ink text-white shadow-lift">
        <div className="flex flex-col gap-6 p-6 lg:flex-row lg:items-end lg:justify-between lg:p-8">
          <div className="min-w-0">
            <Link to="/" className="text-[10px] font-bold uppercase tracking-[0.18em] text-lime/65 transition hover:text-lime">← Dashboard</Link>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              {document ? <DocumentStatusBadge status={document.status} /> : null}
              <span className="font-mono text-[10px] text-white/35">{id}</span>
            </div>
            <h1 className="mt-3 truncate text-2xl font-semibold tracking-tight sm:text-3xl">{document?.original_filename ?? 'Document unavailable'}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-white/50">Inspect every page with its enhanced scan, local OCR output, confidence, extracted entities, and processing metadata.</p>
          </div>

          <div className="flex flex-wrap gap-2">
            {canStart ? (
              <button type="button" onClick={startConversion} disabled={starting} className="rounded-full bg-lime px-5 py-2.5 text-sm font-bold text-ink transition hover:bg-white disabled:cursor-wait disabled:opacity-60">{starting ? 'Starting…' : actionLabel}</button>
            ) : null}
            <button type="button" onClick={refresh} className="rounded-full border border-white/15 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">Refresh</button>
            <Link to="/upload" className="rounded-full border border-white/15 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">Upload another</Link>
          </div>
        </div>

        <div className="grid grid-cols-2 border-t border-white/10 sm:grid-cols-4">
          {[
            ['Pages', document?.page_count ?? 0],
            ['OCR complete', `${document?.ocr_page_count ?? 0}/${document?.page_count ?? 0}`],
            ['Entities', document?.entity_count ?? 0],
            ['Created', document?.created_at ? new Date(document.created_at).toLocaleDateString() : '—'],
          ].map(([label, value]) => (
            <div key={label} className="border-r border-white/10 px-5 py-4 last:border-r-0">
              <p className="text-[9px] font-bold uppercase tracking-[0.16em] text-white/35">{label}</p>
              <p className="mt-1 text-sm font-semibold text-white">{value}</p>
            </div>
          ))}
        </div>
      </header>

      {isProcessing ? (
        <div className="mt-4 flex items-center gap-3 rounded-2xl border border-moss/15 bg-lime/20 px-5 py-3 text-sm font-semibold text-ink" aria-live="polite">
          <span className="h-2 w-2 animate-pulse rounded-full bg-moss" />
          {processingMessage(document)}
        </div>
      ) : null}

      {error || pageError ? (
        <div role="alert" className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">{error || pageError}</div>
      ) : null}

      {document?.status === 'FAILED' && document.error_message ? (
        <div className="mt-4 rounded-2xl border border-rose-200 bg-white/70 px-5 py-4">
          <p className="text-[10px] font-bold uppercase tracking-wide text-rose-700">Processing error</p>
          <p className="mt-1 text-sm text-ink/65">{document.error_message}</p>
        </div>
      ) : null}

      {pages.length ? (
        <div className="mt-5 grid items-start gap-4 lg:grid-cols-[11.5rem_minmax(0,1fr)_23rem] xl:grid-cols-[12.5rem_minmax(0,1fr)_26rem]">
          <WorkspacePageRail pages={pages} selectedPageNumber={selectedPageNumber} onSelect={selectPage} />
          <WorkspaceDocumentViewer
            documentId={id}
            page={selectedPage}
            loading={pageLoading}
            variant={variant}
            onVariantChange={setVariant}
            onPrevious={() => selectPage(pages[selectedIndex - 1].page_number)}
            onNext={() => selectPage(pages[selectedIndex + 1].page_number)}
            hasPrevious={selectedIndex > 0}
            hasNext={selectedIndex >= 0 && selectedIndex < pages.length - 1}
            showOverlays={showOverlays}
            onToggleOverlays={() => setShowOverlays((current) => !current)}
            highlightedEntity={highlightedEntity}
          />
          <WorkspaceInsights
            document={document}
            page={selectedPage}
            entities={entities}
            onEntitySelect={selectEntity}
            selectedEntityId={highlightedEntity?.id}
          />
        </div>
      ) : (
        <section className="mt-5 grid min-h-80 place-items-center rounded-[1.5rem] border border-dashed border-ink/15 bg-white/45 p-8 text-center">
          <div>
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-ink text-sm font-bold text-lime">01</div>
            <h2 className="mt-4 text-xl font-semibold text-ink">Your document workspace is ready</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-ink/50">Start processing to render the scanned pages and populate this workspace with OCR text and extracted entities.</p>
          </div>
        </section>
      )}
    </div>
  )
}

export default DocumentUploadedPage
