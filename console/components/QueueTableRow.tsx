"use client"

import { useRouter } from "next/navigation"

interface Props {
  href: string
  children: React.ReactNode
}

export function QueueTableRow({ href, children }: Props) {
  const router = useRouter()
  return (
    <tr
      className="hover:bg-[#F8F5EE] transition-colors cursor-pointer"
      onClick={() => router.push(href)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          router.push(href)
        }
      }}
      tabIndex={0}
      role="link"
      aria-label="Open review"
    >
      {children}
    </tr>
  )
}
