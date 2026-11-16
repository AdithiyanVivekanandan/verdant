"use client"

import { useTranslation } from "react-i18next"
import { AlertTriangle, CheckCircle2, CircleHelp, Info, ShieldAlert } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useLanguage } from "@/components/layout/i18n-provider"
import { ageLabel } from "@/lib/status"
import { formatDateTime, formatNumber } from "@/lib/utils"
import type { Guidance } from "@/lib/types"

const CONFIDENCE_KEY: Record<string, string> = {
  high: "guidance.confidenceHigh",
  medium: "guidance.confidenceMedium",
  low: "guidance.confidenceLow",
}

export function GuidancePanel({ guidance, headingLevel = 2 }: { guidance: Guidance; headingLevel?: 2 | 3 }) {
  const { t, i18n } = useTranslation()
  const { language } = useLanguage()
  const Heading = headingLevel === 2 ? "h2" : "h3"
  const statusIcon =
    guidance.status === "critical" ? (
      <ShieldAlert className="h-5 w-5 text-destructive" aria-hidden="true" />
    ) : guidance.status === "healthy" ? (
      <CheckCircle2 className="h-5 w-5 text-healthy" aria-hidden="true" />
    ) : (
      <AlertTriangle className="h-5 w-5 text-caution" aria-hidden="true" />
    )

  return (
    <section className="space-y-4" aria-labelledby={`guidance-${guidance.field_id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {statusIcon}
          <div>
            <Heading id={`guidance-${guidance.field_id}`} className="text-lg font-semibold">
              {guidance.headline}
            </Heading>
            <p className="mt-1 text-sm text-muted-foreground">
              {t("guidance.forField", { field: guidance.field_name })} ·{" "}
              {t("guidance.generated")} {formatDateTime(guidance.generated_at, i18n.language)}
            </p>
          </div>
        </div>
        <Badge variant={guidance.status === "critical" ? "destructive" : guidance.status === "healthy" ? "healthy" : "caution"}>
          {t(CONFIDENCE_KEY[guidance.confidence] || "guidance.confidenceLow")} {t("guidance.confidence")}
        </Badge>
      </div>

      <div className="rounded-md border border-input bg-muted/30 p-3">
        <p className="text-sm">
          <span className="font-semibold">{t("common.why")}: </span>
          {guidance.explanation}
        </p>
      </div>

      <div>
        <p className="text-sm font-semibold">{t("common.whatToDo")}</p>
        <ul className="mt-2 space-y-1.5 text-sm">
          {guidance.actions.map((action) => (
            <li key={action} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />
              <span>{action}</span>
            </li>
          ))}
        </ul>
      </div>

      <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <div>
          <dt className="text-xs text-muted-foreground">{t("guidance.targetBand")}</dt>
          <dd className="font-medium">
            {formatNumber(guidance.thresholds.low, i18n.language)}–{formatNumber(guidance.thresholds.high, i18n.language)}%
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">{t("guidance.readingUsed")}</dt>
          <dd className="font-medium">
            {guidance.inputs.moisture_percentage == null
              ? t("common.noData")
              : `${formatNumber(guidance.inputs.moisture_percentage, i18n.language)}%`}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">{t("fieldDetail.lastReading")}</dt>
          <dd className="font-medium">
            {guidance.inputs.recorded_at ? ageLabel(t, guidance.inputs.age_hours) : t("freshness.missing")}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">{t("common.sensor")}</dt>
          <dd className="font-medium">{guidance.inputs.sensor_identifier || t("fields.card.noSensor")}</dd>
        </div>
      </dl>

      {guidance.inputs.weather && (
        <p className="flex items-start gap-2 rounded-md border border-info/30 bg-info/5 p-3 text-sm">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-info" aria-hidden="true" />
          <span>
            {t("guidance.weatherUsed", {
              rain: Math.round(guidance.inputs.weather.rainfall_probability),
              temp: Math.round(guidance.inputs.weather.temperature),
            })}
          </span>
        </p>
      )}

      {language !== "en" && guidance.review_required && (
        <p className="flex items-start gap-2 rounded-md border border-caution/40 bg-caution/10 p-3 text-sm">
          <CircleHelp className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          <span>{guidance.review_note}</span>
        </p>
      )}

      <details className="rounded-md border border-input p-3">
        <summary className="cursor-pointer text-sm font-medium">{t("guidance.limitations")}</summary>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
          {guidance.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </details>
    </section>
  )
}
