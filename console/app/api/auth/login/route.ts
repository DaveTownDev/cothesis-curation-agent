import { NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"
import { timingSafeEqual } from "crypto"

const SESSION_COOKIE = "cothesis_session"
const ATTEMPTS_COOKIE = "cothesis_login_attempts"
const MAX_ATTEMPTS = 5
const LOCKOUT_SECONDS = 15 * 60

function redirectBase(req: NextRequest): string {
  const configured = process.env.CONSOLE_PUBLIC_URL?.replace(/\/$/, "")
  if (configured) return configured
  return req.nextUrl.origin
}

function passcodesMatch(provided: string, secret: string): boolean {
  const a = Buffer.from(provided)
  const b = Buffer.from(secret)
  if (a.length !== b.length) return false
  return timingSafeEqual(a, b)
}

function isLockedOut(attemptsRaw: string | undefined): boolean {
  if (!attemptsRaw) return false
  try {
    const { until } = JSON.parse(attemptsRaw) as { count: number; until: number }
    return until > 0 && Date.now() < until
  } catch {
    return false
  }
}

function nextAttempts(attemptsRaw: string | undefined, failed: boolean): string {
  const now = Date.now()
  let count = 0
  if (attemptsRaw) {
    try {
      const parsed = JSON.parse(attemptsRaw) as { count: number; until: number }
      if (now < parsed.until) count = parsed.count
    } catch {
      count = 0
    }
  }
  if (!failed) return JSON.stringify({ count: 0, until: 0 })
  const next = count + 1
  const until = next >= MAX_ATTEMPTS ? now + LOCKOUT_SECONDS * 1000 : 0
  return JSON.stringify({ count: next, until })
}

export async function POST(req: NextRequest) {
  const formData = await req.formData()
  const passcode = formData.get("passcode") as string | null
  const base = redirectBase(req)

  const secret = process.env.CONSOLE_LOGIN_SECRET
  if (!secret) {
    return NextResponse.redirect(`${base}/login?error=1`)
  }

  const attemptsCookie = req.cookies.get(ATTEMPTS_COOKIE)?.value
  if (isLockedOut(attemptsCookie)) {
    return NextResponse.redirect(`${base}/login?error=locked`)
  }

  if (passcode && passcodesMatch(passcode, secret)) {
    const cookieStore = await cookies()
    cookieStore.set(SESSION_COOKIE, "authenticated", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 8,
      path: "/",
    })
    const ok = NextResponse.redirect(`${base}/dashboard`)
    ok.cookies.set(ATTEMPTS_COOKIE, nextAttempts(attemptsCookie, false), {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: LOCKOUT_SECONDS,
      path: "/",
    })
    return ok
  }

  const fail = NextResponse.redirect(`${base}/login?error=1`)
  fail.cookies.set(ATTEMPTS_COOKIE, nextAttempts(attemptsCookie, true), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: LOCKOUT_SECONDS,
    path: "/",
  })
  return fail
}
