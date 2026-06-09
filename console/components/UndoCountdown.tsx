"use client"

import { useEffect, useRef, useState, type ReactNode } from "react"

interface Props {
  seconds: number
  onExpire: () => void
  children: (secondsLeft: number) => ReactNode
}

/** Counts down from `seconds`; remount with a new `key` to restart. */
export function UndoCountdown({ seconds, onExpire, children }: Props) {
  const [left, setLeft] = useState(seconds)
  const onExpireRef = useRef(onExpire)

  useEffect(() => {
    onExpireRef.current = onExpire
  }, [onExpire])

  useEffect(() => {
    if (left <= 0) {
      onExpireRef.current()
      return
    }
    const t = setTimeout(() => setLeft((n) => n - 1), 1000)
    return () => clearTimeout(t)
  }, [left])

  return <>{children(left)}</>
}
