"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/review", label: "Queue" },
  { href: "/resources", label: "Published" },
  { href: "/pipeline", label: "Pipeline" },
]

export function NavBar() {
  const path = usePathname()
  return (
    <nav className="flex items-center gap-1 ml-6">
      {NAV.map(({ href, label }) => {
        const active = path === href || (href !== "/dashboard" && path.startsWith(href))
        return (
          <Link
            key={href}
            href={href}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
              active
                ? "bg-[#289642]/20 text-white"
                : "text-[#a8c4b0] hover:text-white hover:bg-white/10"
            }`}
          >
            {label}
          </Link>
        )
      })}
    </nav>
  )
}
