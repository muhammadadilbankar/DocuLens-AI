import { getPageImageUrl } from '../services/api.js'

function WorkspacePageRail({ pages, selectedPageNumber, onSelect }) {
  return (
    <aside className="rounded-[1.5rem] border border-ink/10 bg-white/70 p-3 shadow-sm backdrop-blur">
      <div className="flex items-center justify-between px-2 pb-3">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-moss/60">Document</p>
          <h2 className="text-sm font-semibold text-ink">Pages</h2>
        </div>
        <span className="rounded-full bg-ink/5 px-2.5 py-1 text-[10px] font-bold text-ink/50">{pages.length}</span>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-1 lg:max-h-[calc(100vh-18rem)] lg:flex-col lg:overflow-y-auto lg:overflow-x-hidden lg:pr-1">
        {pages.map((page) => {
          const isSelected = page.page_number === selectedPageNumber
          const imagePath = page.preprocessed_image_url ?? page.image_url
          return (
            <button
              key={page.id}
              type="button"
              onClick={() => onSelect(page.page_number)}
              aria-pressed={isSelected}
              aria-label={`Select page ${page.page_number}`}
              className={`group w-28 shrink-0 rounded-xl border p-2 text-left transition lg:w-full ${isSelected ? 'border-moss bg-lime/20 shadow-sm' : 'border-transparent bg-ink/[0.035] hover:border-ink/15 hover:bg-white'}`}
            >
              <div className="aspect-[3/4] overflow-hidden rounded-lg bg-white shadow-sm">
                <img
                  src={getPageImageUrl(imagePath)}
                  alt=""
                  loading="lazy"
                  className="h-full w-full object-cover object-top transition duration-300 group-hover:scale-[1.02]"
                />
              </div>
              <div className="mt-2 flex items-center justify-between gap-2 px-0.5">
                <span className="text-xs font-bold text-ink">Page {page.page_number}</span>
                {page.ocr_completed ? (
                  <span className="text-[9px] font-bold text-moss">{Math.round((page.average_ocr_confidence ?? 0) * 100)}%</span>
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" aria-label="OCR pending" />
                )}
              </div>
            </button>
          )
        })}
      </div>
    </aside>
  )
}

export default WorkspacePageRail
