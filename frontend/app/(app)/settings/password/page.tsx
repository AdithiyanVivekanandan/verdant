"use client"

import { useState } from "react"
import { useTranslation } from "react-i18next"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Lock, ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

export default function ChangePasswordPage() {
  const { t } = useTranslation()
  const router = useRouter()
  const supabase = createBrowserSupabaseClient()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    if (newPassword !== confirmPassword) {
      setError(t("common.passwordsDoNotMatch"))
      return
    }
    setLoading(true)
    try {
      const { error: supabaseError } = await supabase.auth.updateUser({
        password: newPassword,
      })
      if (supabaseError) throw supabaseError
      setSuccess(t("settings.updated"))
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
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
            <Lock className="w-8 h-8 text-primary-foreground" />
          </div>
          <h2 className="text-2xl font-bold">{t("settings.changePassword")}</h2>
          <p className="text-muted-foreground text-sm">
            Update your account password.
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
            <Label htmlFor="current_password">{t("settings.currentPassword")}</Label>
            <Input
              id="current_password"
              type="password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new_password">{t("settings.newPassword")}</Label>
            <Input
              id="new_password"
              type="password"
              required
              minLength={6}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm_password">{t("settings.confirmNewPassword")}</Label>
            <Input
              id="confirm_password"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full"
            />
          </div>
          <Button type="submit" loading={loading} className="w-full">
            {t("settings.changePassword")}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-foreground/70">
          <ArrowLeft className="w-3 h-3 mr-1 inline" />
          {" "}
          <Link href="/settings" className="text-primary font-medium hover:underline">
            {t("common.back")}
          </Link>
        </p>
      </div>
    </div>
  )
}
