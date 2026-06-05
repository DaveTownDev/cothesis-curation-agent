import { NextRequest, NextResponse } from "next/server"
import { cookies } from "next/headers"

const SESSION_COOKIE = "cothesis_session"

function publicBase(req: NextRequest): string {
  // Cloud Run proxies via x-forwarded-* headers; req.url has the internal 0.0.0.0 address.
  const proto = req.headers.get("x-forwarded-proto") ?? "https"
  const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host") ?? ""
  return `${proto}://${host}`
}

export async function POST(req: NextRequest) {
  const formData = await req.formData()
  const passcode = formData.get("passcode") as string | null
  const base = publicBase(req)

  const secret = process.env.CONSOLE_LOGIN_SECRET
  if (!secret) {
    return NextResponse.redirect(`${base}/login?error=1`)
  }

  if (passcode === secret) {
    const cookieStore = await cookies()
    cookieStore.set(SESSION_COOKIE, "authenticated", {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 8,
      path: "/",
    })
    return NextResponse.redirect(`${base}/dashboard`)
  }

  return NextResponse.redirect(`${base}/login?error=1`)
}
