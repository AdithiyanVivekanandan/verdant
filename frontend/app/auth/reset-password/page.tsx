"use client"

import { useState, useEffect } from "react"
import { useTranslation } from "react-i18next"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Lock, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

export const dynamic = "force-dynamic"

export default function ResetPassword() {
  const { t } = useTranslation()
  const router = useRouter()
  const [searchParams, setSearchParams] = useState<URLSearchParams>(new URLSearchParams())
  useEffect(() => {
    setSearchParams(new URLSearchParams(window.location.search))
  }, [])
  const code = searchParams.get("code")
  const next = searchParams.get("next") ?? "/dashboard"
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [password, setPassword] = useState("")
  const supabase = createBrowserSupabaseClient()

  useEffect(() => {
    if (!code) {
      setError(t("auth.invalidResetLink"))
    }
  }, [code])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      const { error: supabaseError } = await supabase.auth.updateUser({
        password,
      })
      if (supabaseError) throw supabaseError
      setSuccess(t("auth.loginSuccess"))
      setTimeout(() => {
        router.push(`/auth/login?next=${encodeURIComponent(next)}`)
      }, 1500)
    } catch (err: any) {
      setError(err.message || t("errors.somethingWentWrong"))
    } finally {
      setLoading(false)
    }
  }

  if (!code) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="w-full max-w-md">
          <Card className="max-w-sm mx-auto p-8 text-center">
            <CardContent>
              <CardTitle>{t("auth.invalidResetLink")}</CardTitle>
              <p className="text-muted-foreground text-sm mt-2">
                Please use the reset link sent to your email.
              </p>
              <Button
                variant="outline"
                asChild
                className="mt-6 w-auto"
                onClick={() => {}}
              >
                <Link href="/auth/login">{t("auth.loginLink")}</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="rounded-md bg-primary p-3">
            <Lock className="w-8 h-8 text-primary-foreground" />
          </div>
          <h2 className="text-2xl font-bold">{t("auth.resetPassword")}</h2>
          <p className="text-muted-foreground text-sm">
            Enter your new password below.
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

        {!success && (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="password">{t("auth.newPassword")}</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full"
              />
            </div>
            <Button type="submit" loading={loading} className="w-full">
              {t("auth.resetPassword")}
            </Button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-foreground/70">
          <ArrowLeft className="w-3 h-3 mr-1 inline" />
          {" "}
          <Link href="/auth/login" className="text-primary font-medium hover:underline">
            {t("auth.alreadyHaveAccount")}
          </Link>
        </p>
      </div>
    </div>
  )
}
