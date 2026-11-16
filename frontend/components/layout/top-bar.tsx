"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import { Sun, Moon, UserRound } from "lucide-react"
import { Button } from "@/components/ui/button"
import { LanguageSelect } from "@/components/layout/language-select"
import { api } from "@/lib/api"
import type { Profile } from "@/lib/types"

export function TopBar({ pageTitle, breadcrumb }: { pageTitle?: string; breadcrumb?: string }) {
  const { t } = useTranslation()
  const [isDark, setIsDark] = useState(false)
  const [profile, setProfile] = useState<Profile | null>(null)

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"))
    api.get<Profile>("/api/v1/auth/me").then(setProfile).catch(() => setProfile(null))
  }, [])

  const toggleTheme = () => {
    const next = !document.documentElement.classList.contains("dark")
    document.documentElement.classList.toggle("dark", next)
    try {
      localStorage.setItem("theme", next ? "dark" : "light")
    } catch {
      /* storage can be unavailable */
    }
    setIsDark(next)
  }

  const initial = profile?.full_name?.trim()?.charAt(0)?.toUpperCase()

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between gap-3 border-b border-border bg-background px-4 sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary lg:hidden">
          <LeafMark className="h-4 w-4 text-primary-foreground" />
        </div>
        <div className="min-w-0">
          {pageTitle ? (
            <h2 className="truncate text-sm font-semibold">{pageTitle}</h2>
          ) : (
            <span className="truncate text-sm font-semibold lg:hidden">{t("common.appName")}</span>
          )}
          {breadcrumb && <span className="block truncate text-xs text-muted-foreground">{breadcrumb}</span>}
        </div>
      </div>

      <div className="flex items-center gap-1.5 sm:gap-2">
        <LanguageSelect compact className="hidden sm:inline-flex" />
        <Button
          variant="ghost"
          size="icon"
          className="rounded-full"
          onClick={toggleTheme}
          aria-label={t("common.theme")}
          aria-pressed={isDark}
        >
          {isDark ? <Moon className="h-4 w-4" aria-hidden="true" /> : <Sun className="h-4 w-4" aria-hidden="true" />}
        </Button>
        <Link
          href="/settings"
          className="flex h-9 items-center gap-2 rounded-full border border-input px-2.5 text-sm hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label={t("nav.accountSettings")}
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-xs font-semibold">
            {initial || <UserRound className="h-3.5 w-3.5" aria-hidden="true" />}
          </span>
          <span className="hidden max-w-[10rem] truncate sm:inline">
            {profile?.full_name || t("nav.account")}
          </span>
        </Link>
      </div>
    </header>
  )
}

function LeafMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" />
      <path d="M2 21c0-3 1.85-5.36 5.08-6" />
    </svg>
  )
}
