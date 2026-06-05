import { redirect } from "next/navigation"
import { setAuthCookie } from "@/lib/auth"
import LoginForm from "./LoginForm"

export default function LoginPage() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <h1 className="font-serif text-3xl font-semibold text-[#0E3A27]">CoThesis</h1>
          <p className="mt-2 text-sm text-[#6b7280]">Curation Console — judges only</p>
        </div>
        <LoginForm />
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
