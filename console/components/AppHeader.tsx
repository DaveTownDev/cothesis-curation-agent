"use client"

import Image from "next/image"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { NavBar } from "@/components/NavBar"

const COMPENDIUM_LIBRARY_URL =
  process.env.NEXT_PUBLIC_COMPENDIUM_URL ??
  "https://compendium-web-production.up.railway.app/library"

export function AppHeader() {
  const pathname = usePathname()
  if (pathname === "/login") return null

  return (
    <header className="hitl-nav-wrapper">
      <nav className="hitl-nav-top" aria-label="CoThesis navigation">
        <div className="hitl-nav-inner">
          <Link href="/dashboard" className="hitl-brand">
            <Image
              src="/cothesis_research_light_bg.svg"
              alt="CoThesis"
              width={140}
              height={22}
              className="hitl-brand-logo"
              priority
            />
            <span className="hitl-brand-divider" aria-hidden />
            <span className="hitl-brand-product">Curation Console</span>
          </Link>

          <div className="hitl-nav-links">
            <a
              href={COMPENDIUM_LIBRARY_URL}
              className="hitl-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              Research Library
            </a>
            <a
              href="https://cothesis.ai/features"
              className="hitl-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              Features
            </a>
            <a
              href="https://cothesis.ai/about"
              className="hitl-nav-link"
              target="_blank"
              rel="noopener noreferrer"
            >
              About
            </a>
          </div>

          <div className="hitl-nav-actions">
            <a
              href={COMPENDIUM_LIBRARY_URL}
              className="hitl-nav-ghost hidden sm:inline-flex"
              target="_blank"
              rel="noopener noreferrer"
            >
              Open Compendium ↗
            </a>
          </div>
        </div>
      </nav>

      <nav className="hitl-subbar" aria-label="Console navigation">
        <div className="hitl-subbar-inner">
          <NavBar />
        </div>
      </nav>
    </header>
  )
}
