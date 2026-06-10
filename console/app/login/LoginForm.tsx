"use client"

import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { Button } from "@/components/ui/button"

function LoginFormInner() {
  const params = useSearchParams()
  const error = params.get("error")

  return (
    <form action="/api/auth/login" method="POST" className="space-y-4">
      <div>
        <label
          htmlFor="passcode"
          className="mb-1 block text-xs font-medium text-[var(--text-primary)]"
        >
          Access passcode
        </label>
        <input
          id="passcode"
          name="passcode"
          type="password"
          autoComplete="current-password"
          required
          className="w-full rounded-[var(--radius-signature)] border border-[var(--border-primary)] bg-white px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-body)] focus:outline-none focus:ring-2 focus:ring-[var(--green-primary)]"
          placeholder="Enter your passcode"
        />
      </div>
      {error === "locked" && (
        <p className="text-xs text-[var(--color-destructive)]">
          Too many attempts — try again in 15 minutes.
        </p>
      )}
      {error && error !== "locked" && (
        <p className="text-xs text-[var(--color-destructive)]">
          Incorrect passcode — please try again.
        </p>
      )}
      <Button type="submit" className="w-full" size="default">
        Sign in
      </Button>
    </form>
  )
}

export default function LoginForm() {
  return (
    <Suspense>
      <LoginFormInner />
    </Suspense>
  )
}
