const stateStyles = {
  loading: {
    dot: 'bg-amber-400 animate-pulse',
    label: 'Checking backend…',
    detail: 'Contacting the local API',
  },
  connected: {
    dot: 'bg-emerald-400',
    label: 'Backend connected',
    detail: 'Local API is healthy',
  },
  disconnected: {
    dot: 'bg-rose-400',
    label: 'Backend unavailable',
    detail: 'Start FastAPI on port 8000',
  },
}

function HealthStatus({ state, health, onRetry }) {
  const display = stateStyles[state]

  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <span className={`h-2.5 w-2.5 rounded-full ring-4 ring-white/10 ${display.dot}`} />
        <div>
          <p className="text-sm font-semibold text-white">{display.label}</p>
          <p className="text-xs text-white/55">
            {health?.service ? `${health.service} · ${health.environment}` : display.detail}
          </p>
        </div>
      </div>
      {state === 'disconnected' && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-xl border border-white/15 px-3 py-2 text-xs font-semibold text-white transition hover:bg-white/10"
        >
          Retry connection
        </button>
      )}
    </div>
  )
}

export default HealthStatus

