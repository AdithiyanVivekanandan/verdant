"use client"

import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useMemo } from "react"
import { useTranslation } from "react-i18next"
import {
  LayoutDashboard,
  Map,
  Activity,
  MoreHorizontal,
  Settings,
  Sun,
  Plus,
  Sprout,
  FileText,
  CircleHelp,
  LogOut,
} from "lucide-react"
import { LanguageSelect } from "@/components/layout/language-select"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"
import { cn } from "@/lib/utils"

const primaryItems = [
  { href: "/dashboard", icon: LayoutDashboard, labelKey: "nav.dashboard" },
  { href: "/fields", icon: Map, labelKey: "nav.myFields" },
  { href: "/readings", icon: Activity, labelKey: "nav.sensorReadings" },
  { href: "/guidance", icon: Sprout, labelKey: "nav.guidance" },
]

const sheetItems = [
  { href: "/fields/new", icon: Plus, labelKey: "nav.registerField" },
  { href: "/weather", icon: Sun, labelKey: "nav.weather" },
  { href: "/reports", icon: FileText, labelKey: "nav.reports" },
  { href: "/help", icon: CircleHelp, labelKey: "nav.help" },
  { href: "/settings", icon: Settings, labelKey: "nav.settings" },
]

function isActive(pathname: string, href: string) {
  if (href === "/fields") {
    return pathname === "/fields" || /^\/fields\/\d+/.test(pathname)
  }
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function MobileNavigation({
  showMoreSheet,
  toggleMoreSheet,
}: {
  showMoreSheet: boolean
  toggleMoreSheet: () => void
}) {
  const { t } = useTranslation()
  const pathname = usePathname()
  const router = useRouter()
  const supabase = useMemo(() => createBrowserSupabaseClient(), [])

  const signOut = async () => {
    toggleMoreSheet()
    await supabase.auth.signOut()
    router.push("/auth/login")
  }

  return (
    <>
      <nav
        className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background pb-[env(safe-area-inset-bottom)] lg:hidden"
        aria-label={t("nav.mainNavigation")}
      >
        <div className="flex items-stretch justify-around">
          {primaryItems.map((item) => {
            const Icon = item.icon
            const active = isActive(pathname, item.href)
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex min-h-[3.5rem] flex-1 flex-col items-center justify-center gap-1 px-1 py-2 text-[11px] leading-tight transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                  active ? "text-primary" : "text-muted-foreground hover:text-foreground",
                )}
                aria-current={active ? "page" : undefined}
              >
                <Icon className={cn("h-5 w-5", active && "text-primary")} aria-hidden="true" />
                <span className={cn(active ? "font-semibold" : "font-normal")}>{t(item.labelKey)}</span>
              </Link>
            )
          })}
          <button
            type="button"
            onClick={toggleMoreSheet}
            className={cn(
              "flex min-h-[3.5rem] flex-1 flex-col items-center justify-center gap-1 px-1 py-2 text-[11px] leading-tight transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              showMoreSheet ? "text-primary" : "text-muted-foreground",
            )}
            aria-expanded={showMoreSheet}
            aria-controls="mobile-more-sheet"
          >
            <MoreHorizontal className="h-5 w-5" aria-hidden="true" />
            <span>{t("nav.more")}</span>
          </button>
        </div>
      </nav>

      <div className={cn("fixed inset-0 z-50 flex items-end lg:hidden", !showMoreSheet && "hidden")}>
        <button
          type="button"
          className="absolute inset-0 bg-foreground/40"
          onClick={toggleMoreSheet}
          aria-label={t("common.close")}
        />
        <div
          id="mobile-more-sheet"
          role="dialog"
          aria-modal="true"
          aria-label={t("nav.more")}
          className="relative w-full rounded-t-xl border-t border-border bg-surface p-4 pb-[calc(1rem+env(safe-area-inset-bottom))] shadow-lg"
        >
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{t("nav.more")}</p>
            <button
              type="button"
              onClick={toggleMoreSheet}
              className="rounded-md px-3 py-1 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              {t("common.close")}
            </button>
          </div>
          <div className="space-y-1">
            {sheetItems.map((item) => {
              const Icon = item.icon
              const active = isActive(pathname, item.href)
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={toggleMoreSheet}
                  className={cn(
                    "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                    active ? "bg-secondary text-secondary-foreground" : "text-foreground hover:bg-accent/50",
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  {t(item.labelKey)}
                </Link>
              )
            })}
            <div className="pt-2">
              <LanguageSelect className="w-full" />
            </div>
            <button
              type="button"
              onClick={signOut}
              className="mt-2 flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-foreground hover:bg-accent/50"
            >
              <LogOut className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              {t("common.logout")}
            </button>
          </div>
        </div>
      </div>
    </>
  )
}
