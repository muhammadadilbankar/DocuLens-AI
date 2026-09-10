import { Link } from 'react-router-dom'

import DocumentImageOverlay from './DocumentImageOverlay.jsx'
import { getPageImageUrl } from '../services/api.js'

function WorkspaceDocumentViewer({ documentId, page, loading, variant, onVariantChange, onPrevious, onNext, hasPrevious, hasNext, showOverlays, onToggleOverlays, highlightedEntity }) {
  const imagePath = variant === 'preprocessed' && page?.preprocessed_image_url
    ? page.preprocessed_image_url
    : page?.image_url
  const canShowOverlays = variant === 'preprocessed' && Boolean(page?.ocr_blocks?.length)
  const highlightedBox = highlightedEntity && page && highlightedEntity.page_number === page.page_number
    ? highlightedEntity.bounding_box
    : null

  return (
    <section className="min-w-0 overflow-hidden rounded-[1.5rem] border border-ink/10 bg-[#e8e5dc] shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/10 bg-white/75 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-2">
          <button
            type="button"
            aria-pressed={showOverlays && canShowOverlays}
            disabled={!canShowOverlays}
            onClick={onToggleOverlays}
            title={variant === 'original' ? 'OCR coordinates align to the enhanced image' : 'Show or hide OCR source regions'}
            className={`rounded-full border px-3 py-2 text-[10px] font-bold transition ${showOverlays && canShowOverlays ? 'border-moss bg-lime/30 text-ink' : 'border-ink/10 bg-white text-ink/55'} disabled:cursor-not-allowed disabled:opacity-35`}
          >
            Regions {showOverlays && canShowOverlays ? 'on' : 'off'}
          </button>
          <button type="button" onClick={onPrevious} disabled={!hasPrevious} aria-label="Previous page" className="grid h-9 w-9 place-items-center rounded-full border border-ink/10 bg-white text-ink transition hover:border-ink/25 disabled:cursor-not-allowed disabled:opacity-30">←</button>
          <div className="min-w-[5.5rem] text-center">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-ink/35">Selected</p>
            <p className="text-sm font-bold text-ink">Page {page?.page_number ?? '—'}</p>
          </div>
          <button type="button" onClick={onNext} disabled={!hasNext} aria-label="Next page" className="grid h-9 w-9 place-items-center rounded-full border border-ink/10 bg-white text-ink transition hover:border-ink/25 disabled:cursor-not-allowed disabled:opacity-30">→</button>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded-full bg-ink/5 p-1" aria-label="Page image version">
            {['original', 'preprocessed'].map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={variant === option}
                disabled={option === 'preprocessed' && !page?.preprocessed_image_url}
                onClick={() => onVariantChange(option)}
                className={`rounded-full px-3 py-1.5 text-[10px] font-bold capitalize transition ${variant === option ? 'bg-white text-ink shadow-sm' : 'text-ink/45 hover:text-ink'} disabled:cursor-not-allowed disabled:opacity-30`}
              >
                {option === 'preprocessed' ? 'Enhanced' : option}
              </button>
            ))}
          </div>
          {page ? <Link to={`/documents/${documentId}/pages/${page.page_number}`} className="rounded-full border border-ink/10 bg-white px-3 py-2 text-[10px] font-bold text-ink transition hover:border-ink/25">Inspect</Link> : null}
        </div>
      </div>

      <div className="relative grid min-h-[32rem] place-items-center p-4 sm:p-6 lg:h-[calc(100vh-22rem)] lg:min-h-[38rem]">
        {loading ? (
          <div className="flex items-center gap-3 text-sm font-semibold text-ink/45"><span className="h-2 w-2 animate-pulse rounded-full bg-moss" />Loading selected page…</div>
        ) : imagePath ? (
          <DocumentImageOverlay
            src={getPageImageUrl(imagePath)}
            alt={`${variant} document page ${page.page_number}`}
            coordinateWidth={page.ocr_coordinate_width}
            coordinateHeight={page.ocr_coordinate_height}
            regions={page.ocr_blocks}
            highlightedBox={highlightedBox}
            overlaysEnabled={canShowOverlays && showOverlays}
            imageClassName="rounded-sm bg-white object-contain shadow-[0_18px_60px_rgba(19,38,32,0.18)]"
          />
        ) : (
          <p className="text-sm font-semibold text-ink/40">No rendered page is available yet.</p>
        )}
      </div>
    </section>
  )
}

export default WorkspaceDocumentViewer
