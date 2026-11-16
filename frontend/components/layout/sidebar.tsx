"use client"

import { useMemo } from "react"
import { usePathname, useRouter } from "next/navigation"
import { useTranslation } from "react-i18next"
import {
  LogOut,
  LayoutDashboard,
  Map,
  Plus,
  Activity,
  Sun,
  Settings,
  ChevronLeft,
  Sprout,
  FileText,
  CircleHelp,
} from "lucide-react"
import { useLanguage } from "@/components/layout/i18n-provider"
import { LanguageSelect } from "@/components/layout/language-select"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, labelKey: "nav.dashboard" },
  { href: "/fields", icon: Map, labelKey: "nav.myFields" },
  { href: "/readings", icon: Activity, labelKey: "nav.sensorReadings" },
  { href: "/guidance", icon: Sprout, labelKey: "nav.guidance" },
  { href: "/weather", icon: Sun, labelKey: "nav.weather" },
  { href: "/reports", icon: FileText, labelKey: "nav.reports" },
]

const bottomItems = [
  { href: "/settings", icon: Settings, labelKey: "nav.settings" },
  { href: "/help", icon: CircleHelp, labelKey: "nav.help" },
]

function isItemActive(pathname: string, href: string) {
  if (href === "/fields") {
    return pathname === "/fields" || /^\/fields\/\d+/.test(pathname)
  }
  return pathname === href || pathname.startsWith(`${href}/`)
}

export function AppSidebar({
  collapsed = false,
  onToggle,
}: {
  collapsed?: boolean
  onToggle?: () => void
}) {
  const { t } = useTranslation()
  const { language } = useLanguage()
  const router = useRouter()
  const supabase = useMemo(() => createBrowserSupabaseClient(), [])
  const pathname = usePathname()

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push("/auth/login")
  }

  const renderItem = (item: { href: string; icon: typeof LayoutDashboard; labelKey: string }) => {
    const Icon = item.icon
    const active = isItemActive(pathname, item.href)
    return (
      <button
        key={item.href}
        type="button"
        onClick={() => router.push(item.href)}
        className={cn(
          "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          active
            ? "bg-secondary text-secondary-foreground"
            : "text-foreground/70 hover:bg-accent/50 hover:text-foreground",
          collapsed && "justify-center px-2",
        )}
        aria-current={active ? "page" : undefined}
        title={collapsed ? t(item.labelKey) : undefined}
      >
        <Icon
          className={cn("h-5 w-5 shrink-0", active ? "text-secondary-foreground" : "text-muted-foreground")}
          aria-hidden="true"
        />
        {!collapsed && <span className="truncate">{t(item.labelKey)}</span>}
      </button>
    )
  }

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-border bg-surface transition-[width] duration-300 lg:flex",
        collapsed ? "w-[76px]" : "w-[248px]",
      )}
      aria-label={t("nav.mainNavigation")}
    >
      <div className={cn("flex items-center gap-2 px-3 py-5", collapsed ? "justify-center" : "justify-between")}>
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-primary">
            <LeafMark className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <span className="truncate text-sm font-semibold tracking-tight">{t("common.appName")}</span>
          )}
        </div>
        {!collapsed && (
          <button
            type="button"
            onClick={onToggle}
            className="rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label={t("nav.collapseSidebar")}
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          type="button"
          onClick={onToggle}
          className="mx-auto mb-2 rounded-md p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          aria-label={t("nav.expandSidebar")}
        >
          <ChevronLeft className="h-4 w-4 rotate-180" aria-hidden="true" />
        </button>
      )}

      <nav className="flex-1 space-y-1 overflow-y-auto px-2" aria-label={t("nav.mainNavigation")}>
        {navItems.map(renderItem)}
        <div className="pt-2">
          {renderItem({ href: "/fields/new", icon: Plus, labelKey: "nav.registerField" })}
        </div>
      </nav>

      <div className="border-t border-border px-3 pb-6 pt-4">
        <div className="space-y-1">
          {bottomItems.map(renderItem)}
          {!collapsed && (
            <div className="pt-2">
              <LanguageSelect className="w-full" compact />
            </div>
          )}
          {collapsed && (
            <p className="py-1 text-center text-[10px] font-medium uppercase text-muted-foreground" lang={language}>
              {language}
            </p>
          )}
          <button
            type="button"
            onClick={handleSignOut}
            className={cn(
              "flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-foreground/70 transition-colors hover:bg-accent/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              collapsed && "justify-center px-2",
            )}
            title={collapsed ? t("common.logout") : undefined}
          >
            <LogOut className="h-5 w-5 shrink-0 text-muted-foreground" aria-hidden="true" />
            {!collapsed && <span className="truncate">{t("common.logout")}</span>}
          </button>
        </div>
      </div>
    </aside>
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
