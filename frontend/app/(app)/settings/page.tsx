"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useTranslation } from "react-i18next"
import { ChevronRight, LogOut, Save, ShieldCheck } from "lucide-react"
import { api } from "@/lib/api"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"
import { useLanguage } from "@/components/layout/i18n-provider"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import type { Language } from "@/lib/i18n"
import type { Profile } from "@/lib/types"

export default function SettingsPage() {
  const { t } = useTranslation()
  const router = useRouter()
  const { language, setLanguage } = useLanguage()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [form, setForm] = useState({ full_name: "", preferred_language: "en" as Language, theme_preference: "system" as "light" | "dark" | "system" })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState("")
  const [error, setError] = useState("")
  const [logoutOpen, setLogoutOpen] = useState(false)

  useEffect(() => {
    api.get<Profile>("/api/v1/auth/me")
      .then((data) => {
        setProfile(data)
        setForm({
          full_name: data.full_name,
          preferred_language: (data.preferred_language as Language) || "en",
          theme_preference: (data.theme_preference as "light" | "dark" | "system") || "system",
        })
      })
      .catch((err: any) => setError(err.message || t("errors.networkError")))
      .finally(() => setLoading(false))
  }, [])

  function applyTheme(theme: "light" | "dark" | "system") {
    localStorage.setItem("theme", theme)
    const dark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)
    document.documentElement.classList.toggle("dark", dark)
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    setSuccess("")
    try {
      const updated = await api.patch<Profile>("/api/v1/auth/me", {
        full_name: form.full_name.trim(),
        preferred_language: form.preferred_language,
        theme_preference: form.theme_preference,
      })
      setProfile(updated)
      setLanguage(form.preferred_language)
      applyTheme(form.theme_preference)
      setSuccess(t("settings.updated"))
    } catch (err: any) {
      setError(typeof err?.body?.detail === "string" ? err.body.detail : t("errors.serverError"))
    } finally {
      setSaving(false)
    }
  }

  async function handleSignOut() {
    await createBrowserSupabaseClient().auth.signOut()
    router.push("/auth/login")
  }

  if (loading) return <p className="py-10 text-sm text-muted-foreground">{t("common.loading")}</p>

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">{t("settings.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("settings.subtitle")}</p>
      </header>

      {error && <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}
      {success && <div role="status" className="rounded-lg border border-healthy/40 bg-healthy/5 p-4 text-sm">{success}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader><CardTitle className="text-lg">{t("settings.profile")}</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="full_name">{t("settings.fullName")}</Label>
              <Input id="full_name" required value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} autoComplete="name" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">{t("settings.email")}</Label>
              <Input id="email" type="email" value={profile?.email || ""} readOnly disabled className="bg-muted/50" />
              <p className="text-xs text-muted-foreground">{t("settings.emailReadOnly")}</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="language">{t("settings.preferredLanguage")}</Label>
              <Select id="language" value={form.preferred_language} onChange={(event) => setForm({ ...form, preferred_language: event.target.value as Language })}>
                <SelectOption value="en">English</SelectOption>
                <SelectOption value="hi">हिन्दी</SelectOption>
                <SelectOption value="kn">ಕನ್ನಡ</SelectOption>
                <SelectOption value="ta">தமிழ்</SelectOption>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="theme">{t("settings.theme")}</Label>
              <Select id="theme" value={form.theme_preference} onChange={(event) => setForm({ ...form, theme_preference: event.target.value as typeof form.theme_preference })}>
                <SelectOption value="system">{t("settings.themeSystem")}</SelectOption>
                <SelectOption value="light">{t("settings.themeLight")}</SelectOption>
                <SelectOption value="dark">{t("settings.themeDark")}</SelectOption>
              </Select>
            </div>
            <Button type="submit" loading={saving}>
              <Save className="mr-1.5 h-4 w-4" aria-hidden="true" />
              {t("common.save")}
            </Button>
          </CardContent>
        </Card>
      </form>

      <Card>
        <CardHeader><CardTitle className="text-lg">{t("settings.account")}</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Link href="/settings/password" className="flex items-center justify-between rounded-md border border-input p-3 text-sm hover:bg-accent">
            <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4" aria-hidden="true" />{t("settings.changePassword")}</span>
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Link href="/onboarding" className="flex items-center justify-between rounded-md border border-input p-3 text-sm hover:bg-accent">
            <span>{t("onboarding.title")}</span>
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          </Link>
          <Separator />
          <Button variant="outline" className="w-full text-destructive" onClick={() => setLogoutOpen(true)}>
            <LogOut className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("settings.logout")}
          </Button>
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">{t("settings.onlySavedPreferences")}</p>

      {logoutOpen && (
        <Dialog role="alertdialog" aria-modal="true" aria-labelledby="logout-title">
          <DialogContent>
            <DialogHeader>
              <DialogTitle id="logout-title">{t("settings.logout")}</DialogTitle>
              <DialogDescription>{t("settings.logoutConfirm")}</DialogDescription>
            </DialogHeader>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setLogoutOpen(false)}>{t("common.cancel")}</Button>
              <Button variant="destructive" onClick={handleSignOut}>{t("settings.logout")}</Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}
