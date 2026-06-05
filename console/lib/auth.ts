import { cookies } from "next/headers"
import { redirect } from "next/navigation"

const SESSION_COOKIE = "cothesis_session"

export async function requireAuth(): Promise<void> {
  const cookieStore = await cookies()
  const session = cookieStore.get(SESSION_COOKIE)
  if (!session?.value || session.value !== "authenticated") {
    redirect("/login")
  }
}

export async function isAuthenticated(): Promise<boolean> {
  const cookieStore = await cookies()
  const session = cookieStore.get(SESSION_COOKIE)
  return session?.value === "authenticated"
}

export async function setAuthCookie(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.set(SESSION_COOKIE, "authenticated", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 8, // 8 hours
    path: "/",
  })
}

export async function clearAuthCookie(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(SESSION_COOKIE)
}
