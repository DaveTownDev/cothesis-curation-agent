"use client"

import { useSearchParams } from "next/navigation"
import { Suspense } from "react"
import { Button } from "@/components/ui/button"

function LoginFormInner() {
  const params = useSearchParams()
  const error = params.get("error")

  return (
    <form
      action="/api/auth/login"
      method="POST"
      className="rounded-xl border border-[#d4cfc5] bg-white p-8 shadow-sm space-y-5"
    >
      <div>
        <label htmlFor="passcode" className="block text-sm font-medium text-[#0E3A27] mb-1.5">
          Access passcode
        </label>
        <input
          id="passcode"
          name="passcode"
          type="password"
          autoComplete="current-password"
          required
          className="w-full rounded-md border border-[#d4cfc5] px-3 py-2 text-sm text-[#0E3A27] placeholder:text-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#289642]"
          placeholder="Enter your passcode"
        />
      </div>
      {error === "locked" && (
        <p className="text-sm text-[#dc2626]">Too many attempts — try again in 15 minutes.</p>
      )}
      {error && error !== "locked" && (
        <p className="text-sm text-[#dc2626]">Incorrect passcode — please try again.</p>
      )}
      <Button type="submit" className="w-full">
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
