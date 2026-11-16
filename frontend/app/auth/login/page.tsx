"use client"

import { useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Mail, Lock, Eye, EyeOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

export const dynamic = "force-dynamic"

export default function Login() {
  const { t } = useTranslation()
  const router = useRouter()
  const [searchParams, setSearchParams] = useState<URLSearchParams>(new URLSearchParams())
  useEffect(() => {
    setSearchParams(new URLSearchParams(window.location.search))
  }, [])
  const redirectTo = searchParams.get("redirectTo") || "/dashboard"
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const supabase = createBrowserSupabaseClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const { data, error: supabaseError } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      if (supabaseError) throw supabaseError
      router.push(redirectTo)
    } catch (err: any) {
      setError(err.message || t("auth.invalidCredentials"))
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignIn = async () => {
    setLoading(true)
    try {
      const { error: supabaseError } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo: `${window.location.origin}/auth/callback?next=${encodeURIComponent(redirectTo)}`,
        },
      })
      if (supabaseError) throw supabaseError
    } catch (err: any) {
      setError(err.message || t("auth.invalidCredentials"))
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
          <div className="lg:w-1/2 flex flex-col items-center justify-center text-center lg:text-left">
            <div className="rounded-md bg-primary p-4 mb-6">
              <svg
                width="32"
                height="32"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-primary-foreground"
              >
                <path d="M12 2L3 7v6c0 5 5 5 5 5h1c4 0 4-4 4-4s0-4 4-4 4 4 4 4c0 0 5 0 5-5V7l-9-5z" />
              </svg>
            </div>
            <h2 className="text-3xl font-bold mb-2">{t("common.appName")}</h2>
            <p className="text-muted-foreground text-sm mb-6">
              Smart Irrigation System for Predictive Water Management and Crop Optimization
            </p>
          </div>

          <div className="w-full lg:w-1/2">
            <div className="flex flex-col items-center justify-center py-8">
              <Card className="w-full max-w-md p-8">
                <CardHeader>
                  <CardTitle className="text-center">{t("auth.loginTitle")}</CardTitle>
                  <p className="text-muted-foreground text-sm text-center">
                    {t("auth.loginSubtitle")}
                  </p>
                </CardHeader>
                <CardContent className="space-y-4">
                  {error && (
                    <div className="p-3 rounded-md border border-destructive bg-destructive/5 text-destructive text-sm">
                      {error}
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
                    <div className="relative space-y-2">
                      <Label htmlFor="password">{t("common.password")}</Label>
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        aria-label="Toggle password visibility"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    <Button type="submit" loading={loading} className="w-full">
                      {t("auth.login")}
                    </Button>
                  </form>
                  <Button
                    variant="outline"
                    onClick={handleGoogleSignIn}
                    loading={loading}
                    className="w-full mt-4"
                  >
                    {t("auth.googleSignIn")}
                  </Button>
                  <div className="relative my-4">
                    <div className="absolute inset-0 flex items-center">
                      <span className="w-full border-t border-input" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                      <span className="bg-background px-2 text-muted-foreground">
                        {t("auth.dividerOr")}
                      </span>
                    </div>
                  </div>
                  <p className="text-center text-sm text-foreground/70">
                    {t("auth.dontHaveAccount")} <Link href="/auth/register" className="text-primary font-medium hover:underline">{t("auth.registerLink")}</Link>
                  </p>
                  <p className="text-center text-sm text-foreground/70">
                    <Link href="/auth/forgot-password" className="text-primary font-medium hover:underline">{t("auth.forgotPassword")}</Link>
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
