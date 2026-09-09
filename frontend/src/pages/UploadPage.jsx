import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { getApiErrorMessage, uploadDocument } from '../services/api.js'

const maxUploadSizeMb = Number(import.meta.env.VITE_MAX_UPLOAD_SIZE_MB ?? 50)
const maxUploadSizeBytes = maxUploadSizeMb * 1024 * 1024

function validatePdf(file) {
  if (!file) return 'Choose a PDF file to continue.'
  if (!file.name.toLowerCase().endsWith('.pdf')) return 'Only PDF files are accepted.'
  if (file.type && file.type !== 'application/pdf') return 'The selected file is not a PDF.'
  if (file.size > maxUploadSizeBytes) return `PDFs must be ${maxUploadSizeMb} MB or smaller.`
  return null
}

function formatFileSize(bytes) {
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

function UploadPage() {
  const inputRef = useRef(null)
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [uploading, setUploading] = useState(false)

  const selectFile = (candidate) => {
    const validationError = validatePdf(candidate)
    setError(validationError ?? '')
    setFile(validationError ? null : candidate)
    setProgress(0)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    selectFile(event.dataTransfer.files[0])
  }

  const handleSubmit = async () => {
    const validationError = validatePdf(file)
    if (validationError) {
      setError(validationError)
      return
    }

    setUploading(true)
    setError('')
    try {
      const document = await uploadDocument(file, setProgress)
      navigate(`/documents/${document.document_id}`, { state: { document } })
    } catch (requestError) {
      setError(getApiErrorMessage(requestError))
      setProgress(0)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-5 py-10 sm:px-8 sm:py-16">
      <div className="mb-9 max-w-2xl">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-moss/65">New document</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.035em] text-ink sm:text-5xl">Bring in a scanned PDF.</h1>
        <p className="mt-4 text-base leading-7 text-ink/55">The original file is stored locally under a private UUID filename. Its contents are never sent to a cloud service.</p>
      </div>

      <section className="rounded-[2rem] border border-ink/10 bg-white/70 p-5 shadow-lift backdrop-blur sm:p-8">
        <div
          onDragEnter={(event) => { event.preventDefault(); setDragging(true) }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          className={`grid min-h-80 place-items-center rounded-[1.5rem] border-2 border-dashed px-6 py-12 text-center transition ${dragging ? 'border-moss bg-lime/25' : 'border-ink/15 bg-parchment/55'}`}
        >
          <div>
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-ink text-lime shadow-lg shadow-ink/10">
              <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" aria-hidden="true">
                <path d="M12 15.5V5m0 0L8 9m4-4 4 4M6 13.5v4.25C6 18.44 6.56 19 7.25 19h9.5c.69 0 1.25-.56 1.25-1.25V13.5" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <h2 className="mt-6 text-xl font-semibold text-ink">Drop your PDF here</h2>
            <p className="mt-2 text-sm text-ink/50">or choose a file up to {maxUploadSizeMb} MB</p>
            <input ref={inputRef} type="file" accept="application/pdf,.pdf" className="sr-only" onChange={(event) => selectFile(event.target.files[0])} />
            <button type="button" onClick={() => inputRef.current?.click()} disabled={uploading} className="mt-6 rounded-full border border-ink/15 bg-white px-5 py-2.5 text-sm font-semibold text-ink transition hover:border-moss hover:text-moss disabled:cursor-not-allowed disabled:opacity-50">
              Choose PDF
            </button>
          </div>
        </div>

        {file && (
          <div className="mt-5 flex flex-col gap-4 rounded-2xl border border-ink/10 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-ink">{file.name}</p>
              <p className="mt-1 text-xs text-ink/45">{formatFileSize(file.size)} · Ready to upload</p>
            </div>
            <button type="button" onClick={() => selectFile(null)} disabled={uploading} className="text-sm font-semibold text-ink/45 hover:text-rose-600 disabled:opacity-40">Remove</button>
          </div>
        )}

        {uploading && (
          <div className="mt-5" aria-live="polite">
            <div className="mb-2 flex justify-between text-xs font-semibold text-ink/55"><span>Uploading securely</span><span>{progress}%</span></div>
            <div className="h-2 overflow-hidden rounded-full bg-ink/10"><div className="h-full rounded-full bg-moss transition-all" style={{ width: `${progress}%` }} /></div>
          </div>
        )}

        {error && <p role="alert" className="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p>}

        <div className="mt-6 flex justify-end">
          <button type="button" onClick={handleSubmit} disabled={!file || uploading} className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-white transition hover:bg-moss disabled:cursor-not-allowed disabled:opacity-35">
            {uploading ? 'Uploading…' : 'Upload document'}
          </button>
        </div>
      </section>
    </div>
  )
}

export default UploadPage
