import { Link, useParams } from 'react-router-dom'

import DocumentStatusBadge from '../components/DocumentStatusBadge.jsx'
import PageGallery from '../components/PageGallery.jsx'
import { useDocumentPages } from '../hooks/useDocumentPages.js'

function DocumentUploadedPage() {
  const { id } = useParams()
  const {
    document,
    pages,
    loading,
    starting,
    pipelineRequested,
    error,
    refresh,
    startConversion,
  } = useDocumentPages(id)
  const isLegacyPagesReady =
    document?.status === 'PREPROCESSING' &&
    pages.length > 0 &&
    !pipelineRequested &&
    pages.every((page) => !page.preprocessed_image_url)
  const isReadyForOcr =
    document?.status === 'OCR_PROCESSING' &&
    pages.length > 0 &&
    !pipelineRequested &&
    pages.some((page) => !page.ocr_completed)

  if (loading) {
    return <div className="mx-auto max-w-7xl px-5 py-20 text-center text-sm font-semibold text-ink/50">Loading document…</div>
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-10 sm:px-8 sm:py-14">
      <section className="rounded-[2rem] bg-ink p-7 text-white shadow-lift sm:p-9">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <div className="mb-5 flex flex-wrap items-center gap-3">
              {document && <DocumentStatusBadge status={document.status} />}
              <span className="font-mono text-[11px] text-white/35">{id}</span>
            </div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-lime/70">Document workspace</p>
            <h1 className="mt-2 truncate text-3xl font-semibold tracking-tight sm:text-4xl">{document?.original_filename ?? 'Document unavailable'}</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-white/55">
              {document?.status === 'EXTRACTING_ENTITIES'
                ? 'PaddleOCR finished locally. Select any page to inspect its text, confidence, and source coordinates.'
                : 'Convert each PDF page, improve scan quality, and preserve both versions for visual comparison.'}
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {(document?.status === 'UPLOADED' || document?.status === 'FAILED' || isLegacyPagesReady || isReadyForOcr) && (
              <button type="button" onClick={startConversion} disabled={starting} className="rounded-full bg-lime px-5 py-2.5 text-sm font-bold text-ink transition hover:bg-white disabled:cursor-wait disabled:opacity-60">
                {starting ? 'Starting…' : document.status === 'FAILED' ? 'Retry processing' : isLegacyPagesReady ? 'Preprocess pages' : isReadyForOcr ? 'Run offline OCR' : 'Process document'}
              </button>
            )}
            <Link to="/upload" className="rounded-full border border-white/15 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10">Upload another</Link>
          </div>
        </div>

        {(document?.status === 'CONVERTING' || (['PREPROCESSING', 'OCR_PROCESSING'].includes(document?.status) && pipelineRequested)) && (
          <div className="mt-8 rounded-2xl border border-white/10 bg-white/5 p-4" aria-live="polite">
            <div className="flex items-center gap-3 text-sm font-semibold"><span className="h-2 w-2 animate-pulse rounded-full bg-lime" />{document.status === 'CONVERTING' ? 'Rendering pages with PyMuPDF…' : document.status === 'PREPROCESSING' ? 'Enhancing pages with OpenCV…' : `Reading pages with PaddleOCR… ${document.ocr_page_count}/${document.page_count}`}</div>
            <p className="mt-1 pl-5 text-xs text-white/45">Large scanned documents may take a moment. This page updates automatically.</p>
          </div>
        )}
      </section>

      {error && (
        <div role="alert" className="mt-6 flex flex-col gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700 sm:flex-row sm:items-center sm:justify-between">
          <span>{error}</span>
          <button type="button" onClick={refresh} className="font-bold underline underline-offset-4">Try again</button>
        </div>
      )}

      {document?.status === 'FAILED' && document.error_message && (
        <div className="mt-6 rounded-2xl border border-rose-200 bg-white/70 p-5">
          <p className="text-xs font-bold uppercase tracking-wide text-rose-700">Conversion error</p>
          <p className="mt-2 text-sm text-ink/65">{document.error_message}</p>
        </div>
      )}

      {pages.length > 0 && <div className="mt-10"><PageGallery documentId={id} pages={pages} /></div>}
    </div>
  )
}

export default DocumentUploadedPage
