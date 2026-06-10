"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { BrandLogo } from "@/components/BrandLogo"
import { NavBar } from "@/components/NavBar"
import { SubBarSlot } from "@/components/SubBarContext"

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
            <BrandLogo />
          </Link>

          <NavBar />

          <div className="hitl-nav-actions">
            <a
              href={COMPENDIUM_LIBRARY_URL}
              className="hitl-nav-cta"
              target="_blank"
              rel="noopener noreferrer"
            >
              Launch Research Directory
            </a>
          </div>
        </div>
      </nav>

      <SubBarSlot />
    </header>
  )
}
