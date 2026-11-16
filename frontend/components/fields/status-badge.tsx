"use client"

import { useTranslation } from "react-i18next"
import { cn } from "@/lib/utils"
import { FRESHNESS_TONE, STATUS_DOT, STATUS_TONE, freshnessLabel, statusLabel } from "@/lib/status"

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const { t } = useTranslation()
  const known = STATUS_TONE[status as keyof typeof STATUS_TONE] || STATUS_TONE.no_data
  const dot = STATUS_DOT[status as keyof typeof STATUS_DOT] || STATUS_DOT.no_data
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold",
        known,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", dot)} aria-hidden="true" />
      {statusLabel(t, status)}
    </span>
  )
}

export function FreshnessBadge({
  freshness,
  className,
}: {
  freshness: string
  className?: string
}) {
  const { t } = useTranslation()
  const tone = FRESHNESS_TONE[freshness as keyof typeof FRESHNESS_TONE] || FRESHNESS_TONE.missing
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium",
        tone,
        className,
      )}
    >
      {freshnessLabel(t, freshness)}
    </span>
  )
}
