import Image from "next/image"
import { cn } from "@/lib/utils"

interface BrandLogoProps {
  className?: string
  markClassName?: string
  /** Wordmark height in Tailwind scale (default matches nav). */
  size?: "nav" | "login"
}

/**
 * CoThesis wordmark (SVG paths) + "Research Library" in Instrument Sans.
 * The source SVG used live text with Geologica, which does not load inside
 * next/image — browsers fall back to Times. HTML text picks up --font-sans.
 */
export function BrandLogo({ className, markClassName, size = "nav" }: BrandLogoProps) {
  const markHeight = size === "login" ? "h-7" : "h-[1.375rem]"
  const suffixSize = size === "login" ? "text-[1.35rem]" : "text-[1.125rem]"

  return (
    <span className={cn("hitl-brand-lockup", suffixSize, className)}>
      <Image
        src="/cothesis_research_light_bg.svg"
        alt=""
        width={size === "login" ? 120 : 100}
        height={size === "login" ? 28 : 22}
        className={cn("hitl-brand-mark w-auto", markHeight, markClassName)}
        priority={size === "login"}
        aria-hidden
      />
      <span className="hitl-brand-suffix" aria-hidden>
        <span className="hitl-brand-bar">|</span>
        Research Library
      </span>
      <span className="sr-only">CoThesis Research Library</span>
    </span>
  )
}
