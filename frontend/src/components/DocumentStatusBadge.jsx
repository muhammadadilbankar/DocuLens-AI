const statusStyles = {
  UPLOADED: 'bg-sky-100 text-sky-800',
  CONVERTING: 'bg-amber-100 text-amber-800',
  PREPROCESSING: 'bg-emerald-100 text-emerald-800',
  FAILED: 'bg-rose-100 text-rose-800',
}

const statusLabels = {
  UPLOADED: 'Uploaded',
  CONVERTING: 'Converting pages',
  PREPROCESSING: 'Pages ready',
  FAILED: 'Conversion failed',
}

function DocumentStatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold ${statusStyles[status] ?? 'bg-ink/5 text-ink/60'}`}>
      {status === 'CONVERTING' && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {statusLabels[status] ?? status}
    </span>
  )
}

export default DocumentStatusBadge
