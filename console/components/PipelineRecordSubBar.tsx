"use client"

import Link from "next/link"
import { useEffect } from "react"
import { Badge } from "@/components/ui/badge"
import { useSubBar } from "@/components/SubBarContext"
import type { EditableResourceSource } from "@/lib/firestore"
import { ArrowLeft } from "lucide-react"

const SOURCE_LABELS: Record<EditableResourceSource, string> = {
  published: "Published",
  archived: "Unpublished",
  draft: "Draft",
  queue: "In review queue",
}

interface Props {
  resourceCode: string
  source: EditableResourceSource
  routing?: string
}

export function PipelineRecordSubBar({ resourceCode, source, routing }: Props) {
  const { setContent } = useSubBar()

  useEffect(() => {
    const left = (
      <div className="flex items-center gap-2 min-w-0">
        <Link href="/pipeline" className="hitl-subbar-back">
          <ArrowLeft size={14} /> Pipeline
        </Link>
        <Badge variant="outline" className="text-[0.6875rem] font-mono truncate max-w-[200px]">
          {resourceCode}
        </Badge>
        <Badge variant="secondary" className="text-[0.6875rem]">{SOURCE_LABELS[source]}</Badge>
        {routing && <Badge variant="outline" className="text-[0.6875rem]">{routing}</Badge>}
      </div>
    )
    setContent({ left, right: null })
    return () => setContent(null)
  }, [resourceCode, source, routing, setContent])

  return null
}
