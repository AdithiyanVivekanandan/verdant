"use client"

import { useEffect, useState } from "react"
import { WifiOff } from "lucide-react"
import { useTranslation } from "react-i18next"

export function OfflineBanner() {
  const { t } = useTranslation()
  const [offline, setOffline] = useState(false)

  useEffect(() => {
    const update = () => setOffline(!navigator.onLine)
    update()
    window.addEventListener("online", update)
    window.addEventListener("offline", update)
    return () => {
      window.removeEventListener("online", update)
      window.removeEventListener("offline", update)
    }
  }, [])

  if (!offline) return null

  return (
    <div
      role="status"
      className="flex items-start gap-2 border-b border-caution/40 bg-caution/15 px-4 py-2 text-sm text-foreground sm:px-6 lg:px-8"
    >
      <WifiOff className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
      <p>
        <span className="font-semibold">{t("connectivity.offlineTitle")}</span>{" "}
        {t("connectivity.offlineBody")}
      </p>
    </div>
  )
}
