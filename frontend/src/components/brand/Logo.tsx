/**
 * Brand mark — Lightning bolt "S" logo inspired by the reference image.
 * Gold metallic lightning bolt on dark background.
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
      {/* Lightning bolt S shape */}
      <path
        d="M20 3 L10 14 H17 L12 29 L24 16 H17 L22 3 Z"
        fill="currentColor"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** Full lockup — mark + wordmark, used in the sidebar header. */
export function LogoLockup({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <div className="w-7 h-7 rounded-lg bg-[#1a1a1a] flex items-center justify-center shrink-0 shadow-lg">
        <LogoMark size={18} className="text-gold" />
      </div>
      <span className="text-body font-medium text-ink-white uppercase tracking-wide">
        SysDesign AI
      </span>
    </div>
  )
}

/** Avatar-style mark — used for the assistant's chat avatar. */
export function LogoAvatar({ size = 32, className = "" }: LogoMarkProps) {
  return (
    <div
      className={`flex items-center justify-center shrink-0 rounded-lg bg-gold ${className}`}
      style={{ width: size, height: size }}
    >
      <LogoMark size={Math.round(size * 0.6)} className="text-surface-black" />
    </div>
  )
}