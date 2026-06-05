import { NextRequest, NextResponse } from "next/server"

const PROTECTED = ["/dashboard", "/review"]
const SESSION_COOKIE = "cothesis_session"

export function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl
  const isProtected = PROTECTED.some((p) => pathname.startsWith(p))
  if (!isProtected) return NextResponse.next()

  const session = req.cookies.get(SESSION_COOKIE)
  if (!session || session.value !== "authenticated") {
    return NextResponse.redirect(new URL("/login", req.url))
  }
  return NextResponse.next()
}

export const config = {
  matcher: ["/dashboard/:path*", "/review/:path*"],
}
