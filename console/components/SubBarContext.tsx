"use client"

import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

export type SubBarContent = {
  left?: ReactNode
  right?: ReactNode
} | null

type SubBarContextValue = {
  content: SubBarContent
  setContent: (content: SubBarContent) => void
}

const SubBarContext = createContext<SubBarContextValue | null>(null)

export function SubBarProvider({ children }: { children: ReactNode }) {
  const [content, setContent] = useState<SubBarContent>(null)
  const value = useMemo(
    () => ({ content, setContent }),
    [content],
  )
  return (
    <SubBarContext.Provider value={value}>{children}</SubBarContext.Provider>
  )
}

export function useSubBar() {
  const ctx = useContext(SubBarContext)
  if (!ctx) throw new Error("useSubBar must be used within SubBarProvider")
  return ctx
}

export function SubBarSlot() {
  const ctx = useContext(SubBarContext)
  const content = ctx?.content
  if (!content?.left && !content?.right) return null

  return (
    <nav className="hitl-subbar" aria-label="Page tools">
      <div className="hitl-subbar-inner hitl-subbar-split">
        <div className="hitl-subbar-left">{content.left}</div>
        <div className="hitl-subbar-right">{content.right}</div>
      </div>
    </nav>
  )
}
