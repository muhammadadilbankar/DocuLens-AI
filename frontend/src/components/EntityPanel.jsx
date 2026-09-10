const typeStyles = {
  PERSON: 'bg-sky-100 text-sky-800',
  ORGANIZATION: 'bg-violet-100 text-violet-800',
  LOCATION: 'bg-emerald-100 text-emerald-800',
  MONEY: 'bg-lime/50 text-ink',
  DATE: 'bg-amber-100 text-amber-800',
  ACCOUNT_NUMBER: 'bg-slate-100 text-slate-700',
}

function EntityPanel({ entities, showPage = true, compact = false, onEntitySelect, selectedEntityId = null }) {
  return (
    <section className={compact ? '' : 'rounded-[1.5rem] border border-ink/10 bg-white/75 p-5 shadow-sm'}>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-moss/60">Local NLP results</p>
          <h2 className={`${compact ? 'text-base' : 'mt-1 text-xl'} font-semibold text-ink`}>Extracted entities</h2>
        </div>
        <span className="rounded-full bg-ink/5 px-3 py-1 text-xs font-bold text-ink/55">{entities.length}</span>
      </div>

      {entities.length ? (
        <div className={`mt-5 grid gap-3 ${compact ? '' : 'sm:grid-cols-2 xl:grid-cols-3'}`}>
          {entities.map((entity) => (
            <button
              key={entity.id}
              type="button"
              disabled={!onEntitySelect}
              aria-pressed={onEntitySelect ? selectedEntityId === entity.id : undefined}
              onClick={() => onEntitySelect?.(entity)}
              className={`w-full rounded-xl border p-3 text-left transition ${selectedEntityId === entity.id ? 'border-amber-400 bg-amber-50 shadow-sm' : 'border-ink/10 bg-parchment/45'} ${onEntitySelect ? 'hover:border-moss/40 hover:bg-lime/10' : 'disabled:opacity-100'}`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className={`rounded-full px-2 py-1 text-[9px] font-bold tracking-wide ${typeStyles[entity.entity_type] ?? 'bg-ink/5 text-ink/60'}`}>
                  {entity.entity_type.replaceAll('_', ' ')}
                </span>
                {showPage ? <span className="text-[10px] font-semibold text-ink/35">Page {entity.page_number}</span> : null}
              </div>
              <p className="mt-2 break-words text-sm font-semibold text-ink">{entity.entity_value}</p>
              <p className="mt-1 text-[10px] uppercase tracking-wide text-ink/35">
                {entity.source}{entity.confidence !== null ? ` · ${Math.round(entity.confidence * 100)}%` : ''}{onEntitySelect && entity.bounding_box ? ' · Locate on page' : ''}
              </p>
            </button>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm leading-6 text-ink/45">No entities have been extracted yet.</p>
      )}
    </section>
  )
}

export default EntityPanel
