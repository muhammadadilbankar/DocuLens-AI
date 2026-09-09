import { getPageImageUrl } from '../services/api.js'

function PageGallery({ pages }) {
  return (
    <section>
      <div className="mb-5 flex items-end justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-moss/60">Converted pages</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-ink">Page inventory</h2>
        </div>
        <span className="rounded-full bg-ink/5 px-3 py-1.5 text-xs font-semibold text-ink/55">{pages.length} pages</span>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {pages.map((page) => (
          <article key={page.id} className="group overflow-hidden rounded-2xl border border-ink/10 bg-white p-2 shadow-sm transition hover:-translate-y-1 hover:shadow-lift">
            <div className="aspect-[3/4] overflow-hidden rounded-xl bg-ink/5">
              <img
                src={getPageImageUrl(page.image_url)}
                alt={`Rendered document page ${page.page_number}`}
                loading="lazy"
                className="h-full w-full object-cover object-top transition duration-300 group-hover:scale-[1.02]"
              />
            </div>
            <div className="flex items-center justify-between px-2 pb-1 pt-3">
              <span className="text-sm font-semibold text-ink">Page {page.page_number}</span>
              <span className="text-[10px] text-ink/40">{page.image_width}×{page.image_height}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  )
}

export default PageGallery
