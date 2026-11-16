import type { FieldStatus, Freshness } from "@/lib/types"

export const STATUS_ORDER: FieldStatus[] = [
  "critical",
  "needs_review",
  "stale",
  "sensor_unavailable",
  "no_data",
  "healthy",
]

export const STATUS_TONE: Record<FieldStatus, string> = {
  critical: "bg-destructive/10 text-destructive border-destructive/30",
  needs_review: "bg-caution/15 text-caution-foreground border-caution/40",
  stale: "bg-muted text-muted-foreground border-border",
  sensor_unavailable: "bg-caution/15 text-caution-foreground border-caution/40",
  no_data: "bg-muted text-muted-foreground border-border",
  healthy: "bg-healthy/10 text-healthy border-healthy/30",
}

export const STATUS_DOT: Record<FieldStatus, string> = {
  critical: "bg-destructive",
  needs_review: "bg-caution",
  stale: "bg-muted-foreground",
  sensor_unavailable: "bg-caution",
  no_data: "bg-muted-foreground",
  healthy: "bg-healthy",
}

export const FRESHNESS_TONE: Record<Freshness, string> = {
  fresh: "bg-healthy/10 text-healthy border-healthy/30",
  delayed: "bg-caution/15 text-caution-foreground border-caution/40",
  stale: "bg-destructive/10 text-destructive border-destructive/30",
  missing: "bg-muted text-muted-foreground border-border",
}

export function statusLabel(t: (key: string) => string, status: string): string {
  const key = `status.${status}`
  return t(key)
}

export function freshnessLabel(t: (key: string) => string, freshness: string): string {
  return t(`freshness.${freshness}`)
}

export function ageLabel(
  t: (key: string, opts?: Record<string, unknown>) => string,
  ageHours: number | null | undefined
): string {
  if (ageHours == null) return t("freshness.missing")
  if (ageHours < 1) {
    const minutes = Math.max(1, Math.round(ageHours * 60))
    return t("common.minutesAgo", { count: minutes })
  }
  if (ageHours < 48) return t("common.hoursAgo", { count: Math.round(ageHours) })
  return t("common.daysAgo", { count: Math.round(ageHours / 24) })
}

export function isAttention(status: string): boolean {
  return status === "critical" || status === "needs_review" || status === "stale" || status === "sensor_unavailable" || status === "no_data"
}
