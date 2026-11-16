"use client"

import { useState } from "react"
import { useTranslation } from "react-i18next"
import { AppSidebar } from "@/components/layout/sidebar"
import { MobileNavigation } from "@/components/layout/mobile-navigation"
import { TopBar } from "@/components/layout/top-bar"
import { PageContainer } from "@/components/layout/page-container"
import { OfflineBanner } from "@/components/layout/offline-banner"

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { t } = useTranslation()
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [showMoreSheet, setShowMoreSheet] = useState(false)

  return (
    <div className="flex min-h-screen bg-background">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        {t("common.skipToContent")}
      </a>
      <AppSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar />
        <OfflineBanner />
        <PageContainer>{children}</PageContainer>
      </div>
      <MobileNavigation
        showMoreSheet={showMoreSheet}
        toggleMoreSheet={() => setShowMoreSheet((prev) => !prev)}
      />
    </div>
  )
}
