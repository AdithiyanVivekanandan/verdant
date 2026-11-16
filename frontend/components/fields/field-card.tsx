"use client"

import Link from "next/link"
import { useTranslation } from "react-i18next"
import { Droplets, MapPin, Radio, Clock } from "lucide-react"
import { Card } from "@/components/ui/card"
import { StatusBadge } from "@/components/fields/status-badge"
import { ageLabel } from "@/lib/status"
import { formatNumber } from "@/lib/utils"
import type { FieldSummary } from "@/lib/types"

export function FieldCard({ field }: { field: FieldSummary }) {
  const { t, i18n } = useTranslation()
  const hasReading = field.latest_moisture != null
  const band =
    field.threshold_low != null && field.threshold_high != null
      ? `${formatNumber(field.threshold_low, i18n.language)}–${formatNumber(field.threshold_high, i18n.language)}%`
      : null

  return (
    <Link
      href={`/fields/${field.id}`}
      className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      <Card className="h-full p-4 transition-colors hover:border-primary/40">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="truncate font-semibold">{field.field_name}</h3>
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {field.crop_type} · {field.area_acres} {t("common.acres")}
            </p>
          </div>
          <StatusBadge status={field.status} />
        </div>

        <div className="mt-4 flex items-end justify-between gap-3">
          <div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold tabular-nums">
                {hasReading ? formatNumber(field.latest_moisture, i18n.language) : "—"}
              </span>
              {hasReading && <span className="text-sm text-muted-foreground">%</span>}
            </div>
            <p className="text-xs text-muted-foreground">{t("common.moisture")}</p>
          </div>
          {band && (
            <p className="text-right text-xs text-muted-foreground">
              {t("guidance.targetBand")}
              <span className="block font-medium text-foreground">{band}</span>
            </p>
          )}
        </div>

        <dl className="mt-4 space-y-1.5 text-xs">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Radio className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <dt className="sr-only">{t("common.sensor")}</dt>
            <dd>{field.sensor_identifier || t("fields.card.noSensor")}</dd>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <Clock className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <dt className="sr-only">{t("common.lastUpdated")}</dt>
            <dd>
              {hasReading
                ? `${t("fieldDetail.lastReading")}: ${ageLabel(t, field.age_hours)}`
                : t("status.sensor_no_readings")}
            </dd>
          </div>
          {field.status_reason === "above_band" && field.latest_moisture != null && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Droplets className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <dd>{t("status.above_band")}</dd>
            </div>
          )}
          {field.status_reason === "below_band" && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Droplets className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <dd>{t("status.below_band")}</dd>
            </div>
          )}
        </dl>
      </Card>
    </Link>
  )
}
