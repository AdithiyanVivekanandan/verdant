"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import {
  Activity,
  AlertCircle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  Clock,
  Droplets,
  Info,
  Map,
  Plus,
  Radio,
  Sprout,
  TrendingUp,
} from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { FieldCard } from "@/components/fields/field-card"
import { StatusBadge } from "@/components/fields/status-badge"
import {
  CropWaterUsageChart,
  FieldWaterUsageChart,
  PlannedVsActualChart,
  WaterConsumptionChart,
  WaterTrendChart,
  formatLitres,
} from "@/components/analytics/water-charts"
import { IrrigationScheduleList } from "@/components/analytics/irrigation-schedule-list"
import { MoistureTrendPanel } from "@/components/analytics/moisture-trend-panel"
import { WeatherImpactPanel } from "@/components/analytics/weather-impact-panel"
import { formatDate, formatDateTime, formatNumber } from "@/lib/utils"
import { ageLabel } from "@/lib/status"
import type {
  DashboardAnalytics,
  DashboardSummary,
  FieldSummary,
  ModelStatus,
  Profile,
  TodaySchedule,
  WeatherCurrent,
  WeatherForecast,
} from "@/lib/types"

export default function DashboardPage() {
  const { t, i18n } = useTranslation()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [summary, setSummary] = useState<DashboardSummary | null>(null)
  const [fields, setFields] = useState<FieldSummary[]>([])
  const [analytics, setAnalytics] = useState<DashboardAnalytics | null>(null)
  const [schedule, setSchedule] = useState<TodaySchedule | null>(null)
  const [model, setModel] = useState<ModelStatus | null>(null)
  const [weather, setWeather] = useState<WeatherCurrent | null>(null)
  const [forecast, setForecast] = useState<WeatherForecast | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const loadData = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [p, s, f, a, sc, ml] = await Promise.all([
        api.get<Profile>("/api/v1/auth/me").catch(() => null),
        api.get<DashboardSummary>("/api/v1/dashboard/summary"),
        api.get<FieldSummary[]>("/api/v1/dashboard/fields"),
        api.get<DashboardAnalytics>("/api/v1/analytics/dashboard").catch(() => null),
        api.get<TodaySchedule>("/api/v1/irrigation/schedule/today").catch(() => null),
        api.get<ModelStatus>("/api/v1/ml/models/status").catch(() => null),
      ])
      setProfile(p)
      setSummary(s)
      setFields(f)
      setAnalytics(a)
      setSchedule(sc)
      setModel(ml)
      if (f.length > 0) {
        api.get<WeatherCurrent>(`/api/v1/weather/current/${f[0].id}`).then(setWeather).catch(() => setWeather(null))
        api.get<WeatherForecast>(`/api/v1/weather/forecast/${f[0].id}`).then(setForecast).catch(() => setForecast(null))
      }
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    loadData()
  }, [loadData])

  const attentionFields = useMemo(
    () => fields.filter((field) => field.requires_attention),
    [fields]
  )

  const actionableSchedule = useMemo(
    () =>
      (schedule?.entries || []).filter(
        (entry) => entry.status === "pending" || entry.status === "accepted"
      ),
    [schedule]
  )

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-9 w-56" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-72 w-full lg:col-span-2" />
          <Skeleton className="h-72 w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">
          {error}
          <button type="button" onClick={loadData} className="ml-2 underline">
            {t("common.retry")}
          </button>
        </div>
      )}

      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("dashboard.greeting", { name: profile?.full_name || t("nav.account") })}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {formatDate(new Date().toISOString(), i18n.language)} · {t("dashboard.subtitle")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href="/readings"><Plus className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("dashboard.addReading")}</Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/fields/new"><Map className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("dashboard.addField")}</Link>
          </Button>
        </div>
      </header>

      {fields.length === 0 ? (
        <EmptyState
          icon={<Sprout className="h-10 w-10" />}
          title={t("dashboard.noFields")}
          description={t("dashboard.noFieldsSubtitle")}
          action={
            <Button asChild>
              <Link href="/fields/new">{t("dashboard.registerFirstField")}</Link>
            </Button>
          }
        />
      ) : (
        <>
          {/* 1. Overview ------------------------------------------------ */}
          <section aria-labelledby="overview-heading" className="space-y-3">
            <h2 id="overview-heading" className="text-lg font-semibold">{t("dashboard.overviewTitle")}</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              <Metric
                label={t("dashboard.totalFields")}
                value={analytics?.total_fields ?? fields.length}
                icon={<Map className="h-5 w-5" aria-hidden="true" />}
                tone="bg-primary/10 text-primary"
              />
              <Metric
                label={t("dashboard.fieldsHealthy")}
                value={analytics?.fields_healthy ?? 0}
                icon={<CheckCircle2 className="h-5 w-5" aria-hidden="true" />}
                tone="bg-healthy/10 text-healthy"
              />
              <Metric
                label={t("dashboard.fieldsNeedingAttention")}
                value={analytics?.fields_requiring_attention ?? 0}
                icon={<AlertCircle className="h-5 w-5" aria-hidden="true" />}
                tone={(analytics?.fields_requiring_attention ?? 0) > 0 ? "bg-caution/15 text-caution-foreground" : "bg-healthy/10 text-healthy"}
              />
              <Metric
                label={t("dashboard.waterUsedToday")}
                value={formatLitres(analytics?.water_usage_today_litres ?? 0)}
                icon={<Droplets className="h-5 w-5" aria-hidden="true" />}
                tone="bg-info/10 text-info"
              />
              <Metric
                label={t("dashboard.scheduledVolumeToday")}
                value={formatLitres(analytics?.scheduled_volume_today_litres ?? 0)}
                icon={<CalendarClock className="h-5 w-5" aria-hidden="true" />}
                tone="bg-secondary/10 text-secondary"
              />
              <Metric
                label={t("dashboard.sensorsReporting")}
                value={analytics?.sensors_reporting_recently ?? 0}
                icon={<Radio className="h-5 w-5" aria-hidden="true" />}
                tone="bg-muted text-muted-foreground"
              />
            </div>
            {analytics && analytics.data_notes.length > 0 && (
              <ul className="space-y-1">
                {analytics.data_notes.map((note) => (
                  <li key={note} className="flex items-start gap-2 text-xs text-muted-foreground">
                    <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                    {note}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* 4. Irrigation schedule ------------------------------------- */}
          <section aria-labelledby="schedule-heading" className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 id="schedule-heading" className="text-lg font-semibold">{t("dashboard.scheduleTitle")}</h2>
              {schedule?.date && <span className="text-sm text-muted-foreground">{schedule.date}</span>}
            </div>
            <Card>
              <CardContent className="space-y-3 pt-4">
                <p className="flex items-start gap-2 rounded-md border border-info/30 bg-info/5 p-3 text-xs text-muted-foreground">
                  <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-info" aria-hidden="true" />
                  {schedule?.decision_support_notice || t("schedule.decisionSupportNotice")}
                </p>
                <IrrigationScheduleList
                  entries={actionableSchedule}
                  onChanged={loadData}
                  emptyTitle={t("schedule.emptyTitle")}
                  emptyDescription={t("schedule.emptyDescription")}
                />
              </CardContent>
            </Card>
          </section>

          <div className="grid gap-4 lg:grid-cols-3">
            {/* 2. Soil moisture trends --------------------------------- */}
            <div className="lg:col-span-2">
              <MoistureTrendPanel fields={fields} />
            </div>

            {/* 5. Weather impact ---------------------------------------- */}
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-lg">{t("dashboard.weatherImpactTitle")}</CardTitle>
                <Link href="/weather" className="text-sm text-primary hover:underline">{t("common.details")}</Link>
              </CardHeader>
              <CardContent>
                <WeatherImpactPanel current={weather} forecast={forecast} />
              </CardContent>
            </Card>
          </div>

          {/* 3. Water consumption analytics ----------------------------- */}
          <section aria-labelledby="water-heading" className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 id="water-heading" className="text-lg font-semibold">{t("dashboard.waterAnalyticsTitle")}</h2>
              <Link href="/reports" className="text-sm text-primary hover:underline">{t("dashboard.viewReports")}</Link>
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.dailyConsumption")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <WaterConsumptionChart data={analytics?.daily_water_series || []} granularity="day" />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.weeklyTrend")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <WaterTrendChart data={analytics?.weekly_water_series || []} granularity="week" />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.fieldWiseUsage")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <FieldWaterUsageChart data={analytics?.field_water_usage || []} />
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.plannedVsActual")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <PlannedVsActualChart data={analytics?.planned_vs_actual || []} />
                </CardContent>
              </Card>
            </div>
          </section>

          {/* 6. Crop and field insights ---------------------------------- */}
          <section aria-labelledby="insights-heading" className="space-y-3">
            <h2 id="insights-heading" className="text-lg font-semibold">{t("dashboard.insightsTitle")}</h2>
            <div className="grid gap-4 lg:grid-cols-3">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.moistureStatusDistribution")}</CardTitle>
                </CardHeader>
                <CardContent>
                  {(analytics?.moisture_status_distribution || []).length === 0 ? (
                    <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
                  ) : (
                    <ul className="space-y-2">
                      {analytics?.moisture_status_distribution.map((item) => {
                        const total = analytics.moisture_status_distribution.reduce((sum, entry) => sum + entry.count, 0)
                        const percent = total > 0 ? Math.round((item.count / total) * 100) : 0
                        return (
                          <li key={item.status}>
                            <div className="flex items-center justify-between text-sm">
                              <span className="flex items-center gap-2">
                                <StatusBadge status={item.status} />
                              </span>
                              <span className="tabular-nums text-muted-foreground">
                                {item.count} ({percent}%)
                              </span>
                            </div>
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.cropWiseUsage")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CropWaterUsageChart data={analytics?.crop_water_usage || []} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.fieldsNeedingMeasurements")}</CardTitle>
                </CardHeader>
                <CardContent>
                  {(analytics?.fields_needing_updated_measurements || []).length === 0 ? (
                    <p className="text-sm text-muted-foreground">{t("analytics.allFieldsUpdated")}</p>
                  ) : (
                    <ul className="space-y-2">
                      {analytics?.fields_needing_updated_measurements.map((item) => (
                        <li key={item.field_id} className="flex items-center justify-between gap-2 text-sm">
                          <Link href={`/fields/${item.field_id}`} className="font-medium hover:underline">
                            {item.field_name}
                          </Link>
                          <span className="text-xs text-muted-foreground">
                            {item.age_hours == null ? t("freshness.missing") : ageLabel(t, item.age_hours)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </section>

          {/* Model transparency ------------------------------------------- */}
          {model && (
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-base">{t("dashboard.modelTransparencyTitle")}</CardTitle>
                <Badge variant={model.status === "validated" ? "healthy" : "caution"}>
                  {t(`model.status.${model.status}`)}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="text-muted-foreground">{model.note}</p>
                <dl className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  <div>
                    <dt className="text-xs text-muted-foreground">{t("model.activePredictor")}</dt>
                    <dd className="font-medium">{model.active_predictor}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">{t("model.trainingSamples")}</dt>
                    <dd className="font-medium tabular-nums">
                      {formatNumber(model.training_samples ?? 0)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">{t("model.requiredSamples")}</dt>
                    <dd className="font-medium tabular-nums">
                      {formatNumber(model.minimum_production_requirements?.min_training_samples ?? 0)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">{t("model.spanDays")}</dt>
                    <dd className="font-medium tabular-nums">
                      {model.minimum_production_requirements?.actual_span_days ?? 0}
                    </dd>
                  </div>
                </dl>
              </CardContent>
            </Card>
          )}

          {/* Fields ------------------------------------------------------ */}
          <section aria-labelledby="fields-heading" className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 id="fields-heading" className="text-lg font-semibold">{t("dashboard.fieldsTitle")}</h2>
              <Link href="/fields" className="text-sm text-primary hover:underline">{t("dashboard.viewAllFields")}</Link>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {fields.map((field) => <FieldCard key={field.id} field={field} />)}
            </div>
          </section>

          {/* Attention list ----------------------------------------------- */}
          {attentionFields.length > 0 && (
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle className="text-lg">{t("dashboard.priorityTitle")}</CardTitle>
                <Link href="/fields" className="text-sm text-primary hover:underline">{t("dashboard.viewAllFields")}</Link>
              </CardHeader>
              <CardContent>
                <ul className="divide-y divide-border">
                  {attentionFields.map((field) => (
                    <li key={field.id} className="py-3 first:pt-0 last:pb-0">
                      <Link href={`/fields/${field.id}`} className="group block rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="flex flex-wrap items-center gap-2 font-medium">
                              {field.field_name}
                              <StatusBadge status={field.status} />
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                              {field.latest_moisture == null
                                ? t("guidance.reason_no_data")
                                : t(`guidance.reason_${field.status_reason}`, {
                                    moisture: field.latest_moisture.toFixed(1),
                                    low: field.threshold_low,
                                    high: field.threshold_high,
                                  })}
                            </p>
                          </div>
                          <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          {/* Recent activity ---------------------------------------------- */}
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-lg">{t("dashboard.recentActivity.title")}</CardTitle>
              <Link href="/readings" className="text-sm text-primary hover:underline">{t("common.details")}</Link>
            </CardHeader>
            <CardContent>
              {(analytics?.recent_irrigation_events || []).length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("analytics.noIrrigationEvents")}</p>
              ) : (
                <ul className="divide-y divide-border">
                  {analytics?.recent_irrigation_events.map((event) => (
                    <li key={event.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5 text-sm first:pt-0 last:pb-0">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                        <span className="font-medium">{event.field_name || `#${event.field_id}`}</span>
                        <span className="text-muted-foreground">
                          {event.water_volume_litres == null
                            ? t("schedule.notRecorded")
                            : formatLitres(event.water_volume_litres)}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatDateTime(event.start_time, i18n.language)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <p className="flex items-center gap-2 text-xs text-muted-foreground">
            <TrendingUp className="h-3.5 w-3.5" aria-hidden="true" />
            {t("analytics.dashboardFootnote")}
          </p>
        </>
      )}
    </div>
  )
}

function Metric({ label, value, icon, tone }: { label: string; value: React.ReactNode; icon: React.ReactNode; tone: string }) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 p-4">
        <div className={`rounded-md p-2 ${tone}`}>{icon}</div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">{label}</p>
          <p className="truncate text-xl font-bold tabular-nums">{value}</p>
        </div>
      </CardContent>
    </Card>
  )
}
