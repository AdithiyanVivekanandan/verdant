"use client"

import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

export default function ForgotPassword() {
  const { t } = useTranslation()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [email, setEmail] = useState("")
  const supabase = createBrowserSupabaseClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      const { error: supabaseError } = await supabase.auth.resetPasswordForEmail(
        email,
        {
          redirectTo: `${window.location.origin}/auth/reset-password`,
        },
      )
      if (supabaseError) throw supabaseError
      setSuccess(t("auth.resetLinkSent"))
    } catch (err: any) {
      setError(err.message || t("errors.somethingWentWrong"))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="rounded-md bg-primary p-3">
            <Mail className="w-8 h-8 text-primary-foreground" />
          </div>
          <h2 className="text-2xl font-bold">{t("auth.forgotPassword")}</h2>
          <p className="text-muted-foreground text-sm">
            {t("auth.resetLinkSent")}
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg border border-destructive bg-destructive/5 text-destructive text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-6 p-4 rounded-lg border border-healthy bg-healthy/5 text-healthy text-sm">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">{t("common.email")}</Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              className="w-full"
            />
          </div>
          <Button type="submit" loading={loading} className="w-full">
            {t("auth.sendResetLink")}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-foreground/70">
          {t("auth.dontHaveAccount")} <Link href="/auth/register" className="text-primary font-medium hover:underline">{t("auth.registerLink")}</Link>
        </p>
        <p className="mt-2 text-center text-sm text-foreground/70">
          {t("auth.alreadyHaveAccount")} <Link href="/auth/login" className="text-primary font-medium hover:underline">{t("auth.loginLink")}</Link>
        </p>
      </div>
    </div>
  )
}
