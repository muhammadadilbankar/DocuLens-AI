import { useState } from 'react'

function polygonPoints(box) {
  return box.map(([x, y]) => `${x},${y}`).join(' ')
}

function boxAnchor(box, width, height) {
  const xs = box.map(([x]) => x)
  const ys = box.map(([, y]) => y)
  return {
    left: `${Math.min(96, Math.max(4, ((Math.min(...xs) + Math.max(...xs)) / 2 / width) * 100))}%`,
    top: `${Math.max(1, (Math.min(...ys) / height) * 100)}%`,
  }
}

function DocumentImageOverlay({
  src,
  alt,
  coordinateWidth,
  coordinateHeight,
  regions = [],
  highlightedBox = null,
  overlaysEnabled = true,
  imageClassName = '',
}) {
  const [hoveredRegion, setHoveredRegion] = useState(null)
  const hasCoordinates = coordinateWidth > 0 && coordinateHeight > 0
  const showOverlay = overlaysEnabled && hasCoordinates
  const tooltipPosition = hoveredRegion
    ? boxAnchor(hoveredRegion.bounding_box, coordinateWidth, coordinateHeight)
    : null

  return (
    <div className="relative inline-block max-h-full max-w-full leading-none">
      <img src={src} alt={alt} className={`block max-h-full max-w-full ${imageClassName}`} />
      {showOverlay ? (
        <svg
          viewBox={`0 0 ${coordinateWidth} ${coordinateHeight}`}
          preserveAspectRatio="none"
          className="pointer-events-none absolute inset-0 h-full w-full overflow-visible"
          aria-label={`${regions.length} OCR source regions`}
        >
          {regions.map((region) => {
            const isHovered = hoveredRegion?.id === region.id
            return (
              <polygon
                key={region.id}
                points={polygonPoints(region.bounding_box)}
                tabIndex={0}
                role="img"
                aria-label={`${region.text}, ${Math.round(region.confidence * 100)} percent confidence`}
                onMouseEnter={() => setHoveredRegion(region)}
                onMouseLeave={() => setHoveredRegion(null)}
                onFocus={() => setHoveredRegion(region)}
                onBlur={() => setHoveredRegion(null)}
                vectorEffect="non-scaling-stroke"
                className={`pointer-events-auto cursor-help stroke-[1.5] transition ${isHovered ? 'fill-lime/30 stroke-moss' : 'fill-sky-300/10 stroke-sky-500/55 hover:fill-lime/25 hover:stroke-moss'}`}
              />
            )
          })}
          {highlightedBox ? (
            <polygon
              points={polygonPoints(highlightedBox)}
              vectorEffect="non-scaling-stroke"
              className="fill-amber-300/35 stroke-amber-500 stroke-[3]"
            />
          ) : null}
        </svg>
      ) : null}

      {showOverlay && hoveredRegion && tooltipPosition ? (
        <div
          className="pointer-events-none absolute z-20 max-w-60 -translate-x-1/2 -translate-y-[calc(100%+0.5rem)] rounded-lg bg-ink px-3 py-2 text-left leading-normal text-white shadow-lift"
          style={tooltipPosition}
          role="tooltip"
        >
          <p className="truncate text-xs font-semibold">{hoveredRegion.text}</p>
          <p className="mt-0.5 text-[9px] font-bold uppercase tracking-wide text-lime">{Math.round(hoveredRegion.confidence * 100)}% confidence</p>
        </div>
      ) : null}
    </div>
  )
}

export default DocumentImageOverlay
