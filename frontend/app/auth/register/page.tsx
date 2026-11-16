"use client"

import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Mail, Lock, Eye, EyeOff } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

const LANGUAGES = [
  { code: "en", name: "English" },
  { code: "hi", name: "हिन्दी" },
  { code: "kn", name: "ಕನ್ನಡ" },
]

export default function Register() {
  const { t } = useTranslation()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
    preferred_language: "en",
    terms: false,
  })
  const [showPassword, setShowPassword] = useState(false)
  const supabase = createBrowserSupabaseClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)
    if (form.password !== form.confirm_password) {
      setError(t("common.passwordsDoNotMatch"))
      setLoading(false)
      return
    }
    if (!form.terms) {
      setError(t("auth.termsRequired"))
      setLoading(false)
      return
    }
    try {
      const { data, error: supabaseError } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: {
          data: {
            full_name: form.full_name,
            preferred_language: form.preferred_language,
          },
          emailRedirectTo: `${window.location.origin}/auth/callback`,
        },
      })
      if (supabaseError) throw supabaseError
      router.push("/auth/login?registered=1")
    } catch (err: any) {
      setError(err.message || t("auth.emailExists"))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center gap-2 mb-8">
          <div className="rounded-md bg-primary p-3">
            <svg
              width="28"
              height="28"
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
          <h2 className="text-2xl font-bold">{t("auth.registerTitle")}</h2>
          <p className="text-muted-foreground text-sm">{t("auth.registerSubtitle")}</p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg border border-destructive bg-destructive/5 text-destructive text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full_name">{t("auth.fullName")}</Label>
            <Input
              id="full_name"
              required
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder={t("auth.fullName")}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">{t("common.email")}</Label>
            <Input
              id="email"
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="name@example.com"
              className="w-full"
            />
          </div>
          <div className="relative space-y-2">
            <Label htmlFor="password">{t("auth.password")}</Label>
            <Input
              id="password"
              type={showPassword ? "text" : "password"}
              required
              minLength={6}
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
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
          <div className="relative space-y-2">
            <Label htmlFor="confirm_password">{t("auth.confirmPassword")}</Label>
            <Input
              id="confirm_password"
              type={showPassword ? "text" : "password"}
              required
              value={form.confirm_password}
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
              className="w-full pr-10"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="preferred_language">{t("auth.preferredLanguage")}</Label>
            <Select
              id="preferred_language"
              required
              value={form.preferred_language}
              onChange={(e) => setForm({ ...form, preferred_language: e.target.value })}
              className="w-full"
            >
              {LANGUAGES.map((l) => (
                <SelectOption key={l.code} value={l.code}>
                  {l.name}
                </SelectOption>
              ))}
            </Select>
          </div>
          <div className="flex items-start space-y-2">
            <Checkbox
              id="terms"
              checked={form.terms}
              onCheckedChange={(v) => setForm({ ...form, terms: v })}
            />
            <Label htmlFor="terms" className="text-sm text-foreground/80">
              {t("auth.terms")}
            </Label>
          </div>
          <Button type="submit" loading={loading} className="w-full">
            {t("auth.register")}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-foreground/70">
          {t("auth.alreadyHaveAccount")} <Link href="/auth/login" className="text-primary font-medium hover:underline">{t("auth.loginLink")}</Link>
        </p>
      </div>
    </div>
  )
}
