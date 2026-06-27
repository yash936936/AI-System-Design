/**
 * Brand mark — replaces the placeholder "S"-in-a-hexagon glyph used
 * throughout the product (sidebar header, chat avatar, empty state).
 *
 * The mark is a hexagon frame (the existing brand "geometric DNA")
 * containing a small node graph — three connected nodes — which reads
 * as "system architecture" at a glance and stays legible at 16–64px.
 * Pure SVG, no emoji, single-color via `currentColor` so it can be
 * recolored with text-* utility classes.
 */

interface LogoMarkProps {
  size?: number
  className?: string
}

export function LogoMark({ size = 20, className = "" }: LogoMarkProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="SysDesign AI"
      className={className}
    >
      {/* Hexagon frame — brand geometric DNA */}
      <path
        d="M16 1.6 L29.2 8.8 V23.2 L16 30.4 L2.8 23.2 V8.8 Z"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinejoin="round"
        fill="none"
      />
      {/* Node graph — architecture / system design */}
      <path
        d="M16 12.3 L10.2 18.4 M16 12.3 L21.8 18.4 M10.2 19.6 H21.8"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <circle cx="16" cy="10.4" r="2.3" fill="currentColor" />
      <circle cx="9.4" cy="20.6" r="2.3" fill="currentColor" />
      <circle cx="22.6" cy="20.6" r="2.3" fill="currentColor" />
    </svg>
  )
}

/** Full lockup — mark + wordmark, used in the sidebar header. */
export function LogoLockup({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <LogoMark size={20} className="text-gold shrink-0" />
      <span className="text-body font-medium text-ink-white uppercase tracking-wide">
        SysDesign AI
      </span>
    </div>
  )
}

/** Avatar-style mark on a filled gold hexagon — used for the assistant's
 *  chat avatar in place of the old "S" letterform. */
export function LogoAvatar({ size = 32, className = "" }: LogoMarkProps) {
  return (
    <div
      className={`hexagon bg-gold flex items-center justify-center shrink-0 ${className}`}
      style={{ width: size, height: size }}
    >
      <LogoMark size={Math.round(size * 0.62)} className="text-surface-black" />
    </div>
  )
}
