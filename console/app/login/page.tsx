import { redirect } from "next/navigation"
import { BrandLogo } from "@/components/BrandLogo"
import { setAuthCookie } from "@/lib/auth"
import LoginForm from "./LoginForm"

export default function LoginPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-3">
          <BrandLogo size="login" className="mx-auto" />
          <div>
            <p className="hitl-eyebrow">Internal tool</p>
            <h1 className="hitl-page-title mt-1">Curation Console</h1>
            <p className="hitl-page-subtitle">Judges &amp; curators only</p>
          </div>
        </div>
        <div className="hitl-card p-5">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}

export async function loginAction(formData: FormData) {
  "use server"
  const passcode = formData.get("passcode") as string
  const secret = process.env.CONSOLE_LOGIN_SECRET
  if (!secret) throw new Error("CONSOLE_LOGIN_SECRET not configured")
  if (passcode === secret) {
    await setAuthCookie()
    redirect("/dashboard")
  }
  redirect("/login?error=1")
}
