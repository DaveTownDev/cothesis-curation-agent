"use client"

import { useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { useSubBar } from "@/components/SubBarContext"

export function PipelineSubBar({ count }: { count: number }) {
  const { setContent } = useSubBar()

  useEffect(() => {
    const right = (
      <Badge variant="secondary" className="text-[0.6875rem]">
        {count} records
      </Badge>
    )

    setContent({ right })
    return () => setContent(null)
  }, [count, setContent])

  return null
}
