import { twMerge } from "tailwind-merge"

export const cn = (...classes: (string | undefined | null | false)[]): string =>
  twMerge(classes.filter(Boolean).join(" "))

export const formatDate = (iso?: string | null, locale = "en"): string => {
  if (!iso) return "—"
  const d = new Date(iso)
  if (isNaN(d.getTime())) return "—"
  const map: Record<string, string> = {
    en: "en-US",
    hi: "hi-IN",
    kn: "kn-IN",
    ta: "ta-IN",
  }
  return d.toLocaleDateString(map[locale] || "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  })
}

export const formatDateTime = (iso?: string | null, locale = "en"): string => {
  if (!iso) return "—"
  const d = new Date(iso)
  if (isNaN(d.getTime())) return "—"
  const map: Record<string, string> = {
    en: "en-US",
    hi: "hi-IN",
    kn: "kn-IN",
    ta: "ta-IN",
  }
  return d.toLocaleString(map[locale] || "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export const formatNumber = (n: number | null | undefined, locale = "en"): string => {
  if (n == null) return "—"
  const map: Record<string, string> = {
    en: "en-US",
    hi: "hi-IN",
    kn: "kn-IN",
    ta: "ta-IN",
  }
  return n.toLocaleString(map[locale] || "en-US")
}

export const moistureConditionLabel = (
  moisture: number | null | undefined,
  t: (key: string) => string
): { label: string; color: string } => {
  if (moisture == null) return { label: t("common.unknown"), color: "text-muted-foreground" }
  if (moisture < 30) return { label: t("common.lowMoisture"), color: "text-destructive" }
  if (moisture < 45) return { label: t("common.moderateMoisture"), color: "text-caution" }
  if (moisture <= 75) return { label: t("common.healthyMoisture"), color: "text-healthy" }
  return { label: t("common.highMoisture"), color: "text-info" }
}

export const moistureConditionColor = (
  moisture: number | null | undefined
): string => {
  if (moisture == null) return "bg-muted"
  if (moisture < 30) return "bg-destructive/10"
  if (moisture < 45) return "bg-caution/10"
  if (moisture <= 75) return "bg-healthy/10"
  return "bg-info/10"
}
