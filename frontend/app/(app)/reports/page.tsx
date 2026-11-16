"use client"

import { useCallback, useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import {
  Activity,
  BarChart3,
  CalendarDays,
  Droplets,
  Info,
  Ruler,
  Timer,
} from "lucide-react"
import { api } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import {
  CropWaterUsageChart,
  FieldWaterUsageChart,
  PlannedVsActualChart,
  WaterConsumptionChart,
  WaterTrendChart,
  formatLitres,
} from "@/components/analytics/water-charts"
import { formatDate, formatNumber } from "@/lib/utils"
import type { WaterUsage, WaterUsageTrends } from "@/lib/types"

type Granularity = "day" | "week" | "month"

/**
 * Water usage reports.
 *
 * Every number comes from measured irrigation events. Where nothing has
 * been measured the page shows an explicit empty state instead of a chart
 * with invented data.
 */
export default function ReportsPage() {
  const { t, i18n } = useTranslation()
  const [usage, setUsage] = useState<WaterUsage | null>(null)
  const [trends, setTrends] = useState<WaterUsageTrends | null>(null)
  const [granularity, setGranularity] = useState<Granularity>("day")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [u, tr] = await Promise.all([
        api.get<WaterUsage>("/api/v1/analytics/water-usage"),
        api.get<WaterUsageTrends>("/api/v1/analytics/water-usage/trends?days=30"),
      ])
      setUsage(u)
      setTrends(tr)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    load()
  }, [load])

  const series =
    granularity === "day"
      ? trends?.daily || []
      : granularity === "week"
        ? trends?.weekly || []
        : trends?.monthly || []

  const comparison = trends?.period_comparison

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">{t("analytics.reportsTitle")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("analytics.reportsSubtitle")}</p>
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">
          {error}
          <button type="button" onClick={load} className="ml-2 underline">
            {t("common.retry")}
          </button>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
          </div>
          <Skeleton className="h-72 w-full" />
        </div>
      ) : (
        <>
          {/* Core metrics ------------------------------------------------ */}
          <section aria-labelledby="usage-metrics-heading" className="space-y-3">
            <h2 id="usage-metrics-heading" className="text-lg font-semibold">{t("analytics.coreMetrics")}</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Metric
                label={t("analytics.today")}
                value={formatLitres(trends?.period_totals.today.litres ?? 0)}
                sub={t("analytics.eventsCount", { count: trends?.period_totals.today.events ?? 0 })}
                icon={<Droplets className="h-5 w-5" aria-hidden="true" />}
                tone="bg-info/10 text-info"
              />
              <Metric
                label={t("analytics.thisWeek")}
                value={formatLitres(trends?.period_totals.this_week.litres ?? 0)}
                sub={t("analytics.eventsCount", { count: trends?.period_totals.this_week.events ?? 0 })}
                icon={<CalendarDays className="h-5 w-5" aria-hidden="true" />}
                tone="bg-secondary/10 text-secondary"
              />
              <Metric
                label={t("analytics.thisMonth")}
                value={formatLitres(trends?.period_totals.this_month.litres ?? 0)}
                sub={t("analytics.eventsCount", { count: trends?.period_totals.this_month.events ?? 0 })}
                icon={<BarChart3 className="h-5 w-5" aria-hidden="true" />}
                tone="bg-primary/10 text-primary"
              />
              <Metric
                label={t("analytics.averagePerEvent")}
                value={usage?.average_per_event_litres == null ? "—" : formatLitres(usage.average_per_event_litres)}
                sub={
                  usage?.irrigation_frequency_per_week == null
                    ? t("common.noData")
                    : t("analytics.perWeek", { count: usage.irrigation_frequency_per_week })
                }
                icon={<Timer className="h-5 w-5" aria-hidden="true" />}
                tone="bg-muted text-muted-foreground"
              />
            </div>

            <Card>
              <CardContent className="grid gap-3 p-4 text-sm sm:grid-cols-3">
                <Detail
                  label={t("analytics.litresPerAcre")}
                  value={usage?.litres_per_acre == null ? t("common.noData") : formatNumber(usage.litres_per_acre)}
                />
                <Detail
                  label={t("analytics.averageInterval")}
                  value={usage?.average_per_event_days == null ? t("common.noData") : t("analytics.daysValue", { count: usage.average_per_event_days })}
                />
                <Detail
                  label={t("analytics.unmeasuredEvents")}
                  value={formatNumber(usage?.unmeasured_event_count ?? 0)}
                />
              </CardContent>
            </Card>

            {(usage?.data_notes || []).length > 0 && (
              <ul className="space-y-1">
                {usage?.data_notes.map((note) => (
                  <li key={note} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                    {note}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Consumption series ------------------------------------------ */}
          <section aria-labelledby="consumption-heading" className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 id="consumption-heading" className="text-lg font-semibold">{t("analytics.consumption")}</h2>
              <div className="flex gap-1" role="group" aria-label={t("analytics.granularity")}>
                {(["day", "week", "month"] as const).map((value) => (
                  <Button
                    key={value}
                    variant={granularity === value ? "secondary" : "ghost"}
                    size="sm"
                    aria-pressed={granularity === value}
                    onClick={() => setGranularity(value)}
                  >
                    {t(`analytics.${value}`)}
                  </Button>
                ))}
              </div>
            </div>
            <Card>
              <CardContent className="pt-4">
                <WaterConsumptionChart data={series} granularity={granularity} height={280} />
              </CardContent>
            </Card>
          </section>

          {/* Comparison --------------------------------------------------- */}
          <section aria-labelledby="comparison-heading" className="space-y-3">
            <h2 id="comparison-heading" className="text-lg font-semibold">{t("analytics.comparisons")}</h2>
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.fieldWiseUsage")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <FieldWaterUsageChart data={usage?.by_field || []} />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.cropWiseUsage")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CropWaterUsageChart data={usage?.by_crop || []} />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.plannedVsActual")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <PlannedVsActualChart data={usage?.planned_vs_actual || []} />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.weeklyTrend")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <WaterTrendChart data={trends?.weekly || []} granularity="week" />
                </CardContent>
              </Card>
            </div>

            {comparison && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.periodComparison")}</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-3 text-sm sm:grid-cols-3">
                  <Detail
                    label={t("analytics.previousPeriod")}
                    value={formatLitres(comparison.previous_litres)}
                  />
                  <Detail
                    label={t("analytics.currentPeriod")}
                    value={formatLitres(comparison.current_litres)}
                  />
                  <Detail
                    label={t("analytics.change")}
                    value={
                      comparison.change_litres == null
                        ? t("analytics.noPreviousData")
                        : `${comparison.change_litres > 0 ? "+" : ""}${formatLitres(comparison.change_litres)}${
                            comparison.change_percent != null ? ` (${comparison.change_percent > 0 ? "+" : ""}${comparison.change_percent}%)` : ""
                          }`
                    }
                  />
                </CardContent>
              </Card>
            )}
          </section>

          {/* Measured events --------------------------------------------- */}
          <section aria-labelledby="events-heading" className="space-y-3">
            <h2 id="events-heading" className="text-lg font-semibold">{t("analytics.measuredEventsTitle")}</h2>
            <Card>
              <CardContent className="pt-4">
                {(usage?.by_day || []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">{t("analytics.noMeasuredWater")}</p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-input">
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.date")}</th>
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.waterUsed")}</th>
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.eventsCount", { count: 0 }).replace("0", "#")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usage?.by_day.map((point) => (
                          <tr key={point.date} className="border-b border-input/50">
                            <td className="py-2">{formatDate(point.date, i18n.language)}</td>
                            <td className="py-2 tabular-nums">{formatLitres(point.total_litres)}</td>
                            <td className="py-2 tabular-nums">{point.events}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* Estimated against actual per schedule ------------------------ */}
          {(usage?.estimated_vs_actual || []).length > 0 && (
            <section aria-labelledby="estimate-heading" className="space-y-3">
              <h2 id="estimate-heading" className="text-lg font-semibold">{t("analytics.estimateVsActualTitle")}</h2>
              <Card>
                <CardContent className="pt-4">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b border-input">
                          <th scope="col" className="pb-2 text-muted-foreground">{t("common.field")}</th>
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.date")}</th>
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.planned")}</th>
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.actual")}</th>
                          <th scope="col" className="pb-2 text-muted-foreground">{t("analytics.difference")}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {usage?.estimated_vs_actual.map((row) => (
                          <tr key={row.schedule_id} className="border-b border-input/50">
                            <td className="py-2">{row.field_name || `#${row.field_id}`}</td>
                            <td className="py-2">{row.scheduled_date ? formatDate(row.scheduled_date, i18n.language) : "—"}</td>
                            <td className="py-2 tabular-nums">{row.estimated_litres == null ? "—" : formatLitres(row.estimated_litres)}</td>
                            <td className="py-2 tabular-nums">{row.actual_litres == null ? "—" : formatLitres(row.actual_litres)}</td>
                            <td className="py-2 tabular-nums">
                              {row.difference_percent == null ? "—" : `${row.difference_percent > 0 ? "+" : ""}${row.difference_percent}%`}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </section>
          )}

          <p className="flex items-start gap-2 text-xs text-muted-foreground">
            <Ruler className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            {t("analytics.unitNote")}
          </p>
        </>
      )}
    </div>
  )
}

function Metric({
  label,
  value,
  sub,
  icon,
  tone,
}: {
  label: string
  value: React.ReactNode
  sub?: string
  icon: React.ReactNode
  tone: string
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className={`rounded-md p-2 ${tone}`}>{icon}</div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="truncate text-xl font-bold tabular-nums">{value}</p>
          {sub && <p className="truncate text-xs text-muted-foreground">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="font-medium tabular-nums">{value}</dd>
    </div>
  )
}
