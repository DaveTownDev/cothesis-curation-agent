"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/review", label: "Review queue" },
  { href: "/resources", label: "Published" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/prompt-lab", label: "Prompt lab" },
]

export function NavBar() {
  const path = usePathname()
  return (
    <div className="hitl-nav-main-links">
      {NAV.map(({ href, label }) => {
        const active =
          path === href || (href !== "/dashboard" && path.startsWith(href))
        return (
          <Link
            key={href}
            href={href}
            className={`hitl-nav-link${active ? " is-active" : ""}`}
          >
            {label}
          </Link>
        )
      })}
    </div>
  )
}
