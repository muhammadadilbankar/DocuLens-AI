const statusStyles = {
  UPLOADED: 'bg-sky-100 text-sky-800',
  CONVERTING: 'bg-amber-100 text-amber-800',
  PREPROCESSING: 'bg-amber-100 text-amber-800',
  OCR_PROCESSING: 'bg-amber-100 text-amber-800',
  EXTRACTING_ENTITIES: 'bg-emerald-100 text-emerald-800',
  INDEXING: 'bg-violet-100 text-violet-800',
  COMPLETED: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-rose-100 text-rose-800',
}

const statusLabels = {
  UPLOADED: 'Uploaded',
  CONVERTING: 'Converting pages',
  PREPROCESSING: 'Preprocessing',
  OCR_PROCESSING: 'Reading pages',
  EXTRACTING_ENTITIES: 'Extracting entities',
  INDEXING: 'Building search index',
  COMPLETED: 'Processing complete',
  FAILED: 'Processing failed',
}

function DocumentStatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold ${statusStyles[status] ?? 'bg-ink/5 text-ink/60'}`}>
      {['CONVERTING', 'PREPROCESSING', 'OCR_PROCESSING', 'EXTRACTING_ENTITIES', 'INDEXING'].includes(status) && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {statusLabels[status] ?? status}
    </span>
  )
}

export default DocumentStatusBadge
