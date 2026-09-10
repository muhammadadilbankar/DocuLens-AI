import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import EntityPanel from '../components/EntityPanel.jsx'
import { getApiErrorMessage, getDocumentPage, getPageImageUrl } from '../services/api.js'

function PageInspectorPage() {
  const { id, pageNumber } = useParams()
  const [page, setPage] = useState(null)
  const [variant, setVariant] = useState('preprocessed')
  const [error, setError] = useState('')

  useEffect(() => {
    getDocumentPage(id, pageNumber)
      .then(setPage)
      .catch((requestError) => setError(getApiErrorMessage(requestError)))
  }, [id, pageNumber])

  if (error) {
    return <div role="alert" className="mx-auto max-w-3xl px-5 py-20 text-center text-rose-700">{error}</div>
  }
  if (!page) {
    return <div className="mx-auto max-w-3xl px-5 py-20 text-center text-sm font-semibold text-ink/50">Loading page…</div>
  }

  const imagePath = variant === 'preprocessed' && page.preprocessed_image_url
    ? page.preprocessed_image_url
    : page.image_url

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link to={`/documents/${id}`} className="text-xs font-bold uppercase tracking-[0.16em] text-moss hover:underline">← Document pages</Link>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink">Page {page.page_number}</h1>
        </div>
        <div className="flex items-center gap-3">
          {page.average_ocr_confidence !== null && <span className="rounded-full bg-lime/60 px-3 py-1.5 text-xs font-bold text-ink">{Math.round(page.average_ocr_confidence * 100)}% confidence</span>}
          <div className="flex rounded-full bg-ink/5 p-1">
            {['original', 'preprocessed'].map((option) => (
              <button key={option} type="button" disabled={option === 'preprocessed' && !page.preprocessed_image_url} onClick={() => setVariant(option)} className={`rounded-full px-3 py-1.5 text-xs font-semibold capitalize ${variant === option ? 'bg-white text-ink shadow-sm' : 'text-ink/45'} disabled:opacity-30`}>{option}</button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(22rem,0.85fr)]">
        <section className="overflow-hidden rounded-[1.5rem] border border-ink/10 bg-ink/5 p-3">
          <img src={getPageImageUrl(imagePath)} alt={`${variant} page ${page.page_number}`} className="mx-auto h-auto max-h-[78vh] max-w-full rounded-xl bg-white object-contain shadow-lift" />
        </section>
        <aside className="overflow-hidden rounded-[1.5rem] border border-ink/10 bg-white/75 shadow-lift backdrop-blur">
          <div className="border-b border-ink/10 p-5">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-moss/60">PaddleOCR output</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">Extracted text</h2>
          </div>
          <div className="max-h-[68vh] overflow-y-auto p-5">
            {page.ocr_blocks.length ? (
              <div className="space-y-3">
                {page.ocr_blocks.map((block) => (
                  <div key={block.id} className="rounded-xl border border-ink/10 bg-parchment/55 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm leading-6 text-ink">{block.text}</p>
                      <span className="shrink-0 text-[10px] font-bold text-moss">{Math.round(block.confidence * 100)}%</span>
                    </div>
                    <p className="mt-2 font-mono text-[9px] text-ink/35">Box: {JSON.stringify(block.bounding_box)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm leading-6 text-ink/50">{page.ocr_completed ? 'No readable text was detected on this page.' : 'OCR has not processed this page yet.'}</p>
            )}
          </div>
        </aside>
      </div>
      <div className="mt-6"><EntityPanel entities={page.entities} showPage={false} /></div>
    </div>
  )
}

export default PageInspectorPage
