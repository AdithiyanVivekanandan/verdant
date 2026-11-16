"use client"

import { useCallback, useEffect, useState } from "react"
import { useTranslation } from "react-i18next"
import {
  CalendarClock,
  Droplets,
  Info,
  Layers,
  TrendingDown,
  TrendingUp,
} from "lucide-react"
import { api } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { IrrigationScheduleList } from "@/components/analytics/irrigation-schedule-list"
import { formatLitres } from "@/components/analytics/water-charts"
import { formatDateTime, formatNumber } from "@/lib/utils"
import type {
  FieldIrrigationSettings,
  IrrigationEvent,
  IrrigationSchedule,
  Prediction,
  PredictionHistory,
} from "@/lib/types"

/**
 * The intelligence view of a single field.
 *
 * It shows the irrigation requirement, the prediction history, today's
 * schedule, the recorded irrigation events, the water consumed by this
 * field and the application settings that make a volume estimate possible.
 */
export function FieldIntelligencePanel({
  fieldId,
  fieldName,
  onChanged,
}: {
  fieldId: number
  fieldName: string
  onChanged?: () => void
}) {
  const { t, i18n } = useTranslation()
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [history, setHistory] = useState<PredictionHistory[]>([])
  const [events, setEvents] = useState<IrrigationEvent[]>([])
  const [schedule, setSchedule] = useState<IrrigationSchedule[]>([])
  const [settings, setSettings] = useState<FieldIrrigationSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [p, h, e, s, cfg] = await Promise.all([
        api.get<Prediction>(`/api/v1/irrigation/predictions/${fieldId}`).catch(() => null),
        api.get<PredictionHistory[]>(`/api/v1/irrigation/predictions/${fieldId}/history?limit=20`).catch(() => []),
        api.get<{ items: IrrigationEvent[] }>(`/api/v1/irrigation/events?field_id=${fieldId}&limit=50`).catch(() => ({ items: [] })),
        api.get<IrrigationSchedule[]>(`/api/v1/irrigation/schedule?field_id=${fieldId}&limit=10`).catch(() => []),
        api.get<FieldIrrigationSettings>(`/api/v1/irrigation/fields/${fieldId}/settings`).catch(() => null),
      ])
      setPrediction(p)
      setHistory(Array.isArray(h) ? h : [])
      setEvents(Array.isArray(e?.items) ? e.items : [])
      setSchedule(Array.isArray(s) ? s : [])
      setSettings(cfg)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }, [fieldId, t])

  useEffect(() => {
    load()
  }, [load])

  const totalMeasured = events
    .filter((event) => event.water_volume_litres != null)
    .reduce((sum, event) => sum + (event.water_volume_litres || 0), 0)
  const unmeasuredCount = events.filter((event) => event.water_volume_litres == null).length

  const requirement = prediction?.requirement

  return (
    <div className="space-y-4">
      {error && (
        <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0">
          <CardTitle className="text-lg">{t("fieldDetail.intelligence.requirementTitle")}</CardTitle>
          {prediction && (
            <Badge variant={prediction.provisional ? "caution" : "healthy"}>
              {prediction.provisional
                ? t("model.status.provisional")
                : t("model.status.validated")}
            </Badge>
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          {loading ? (
            <Skeleton className="h-40 w-full" />
          ) : !prediction || prediction.model_status === "no_data" ? (
            <EmptyState
              icon={<Droplets className="h-8 w-8" />}
              title={t("fieldDetail.intelligence.noPrediction")}
              description={t("fieldDetail.intelligence.noPredictionDescription")}
            />
          ) : (
            <>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Metric
                  label={t("fieldDetail.intelligence.currentMoisture")}
                  value={prediction.current_moisture == null ? "—" : `${prediction.current_moisture.toFixed(1)}%`}
                />
                <Metric
                  label={t("fieldDetail.intelligence.predictedMoisture")}
                  value={prediction.predicted_moisture == null ? "—" : `${prediction.predicted_moisture.toFixed(1)}%`}
                  icon={
                    (prediction.moisture_trend_pp_per_day ?? 0) >= 0 ? (
                      <TrendingUp className="h-4 w-4 text-healthy" aria-hidden="true" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-caution" aria-hidden="true" />
                    )
                  }
                />
                <Metric
                  label={t("fieldDetail.intelligence.requirementMm")}
                  value={prediction.irrigation_requirement_mm == null ? "—" : `${prediction.irrigation_requirement_mm.toFixed(1)} mm`}
                />
                <Metric
                  label={t("fieldDetail.intelligence.estimatedVolume")}
                  value={prediction.estimated_volume_litres == null ? "—" : formatLitres(prediction.estimated_volume_litres)}
                />
              </div>

              <div className="rounded-md border border-input bg-muted/30 p-3 text-sm">
                <p className="font-semibold">{t("common.why")}</p>
                <p className="mt-1 text-muted-foreground">{prediction.reason}</p>
              </div>

              <dl className="grid gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs text-muted-foreground">{t("fieldDetail.intelligence.modelSource")}</dt>
                  <dd className="font-medium">
                    {prediction.model_name}
                    {prediction.model_version ? ` · ${prediction.model_version}` : ""}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t("fieldDetail.intelligence.confidence")}</dt>
                  <dd className="font-medium tabular-nums">
                    {Math.round(prediction.confidence * 100)}%
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t("fieldDetail.intelligence.dataFreshness")}</dt>
                  <dd className="font-medium">{t(`freshness.${prediction.data_freshness}`)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t("fieldDetail.intelligence.calculationVersion")}</dt>
                  <dd className="font-medium">{prediction.calculation_version || "—"}</dd>
                </div>
              </dl>

              {requirement && (
                <details className="rounded-md border border-input p-3 text-sm">
                  <summary className="cursor-pointer font-medium">
                    {t("fieldDetail.intelligence.howCalculated")}
                  </summary>
                  <dl className="mt-2 grid gap-2 sm:grid-cols-2">
                    <Detail label={t("fieldDetail.intelligence.rootDepth")} value={requirement.root_depth_mm == null ? "—" : `${requirement.root_depth_mm.toFixed(0)} mm`} />
                    <Detail label={t("fieldDetail.intelligence.cropCoefficient")} value={requirement.kc == null ? "—" : requirement.kc.toFixed(2)} />
                    <Detail label={t("fieldDetail.intelligence.et0")} value={requirement.et0_mm == null ? t("common.noData") : `${requirement.et0_mm.toFixed(2)} mm`} />
                    <Detail label={t("fieldDetail.intelligence.cropWaterUse")} value={requirement.crop_water_use_mm == null ? t("common.noData") : `${requirement.crop_water_use_mm.toFixed(1)} mm`} />
                    <Detail label={t("fieldDetail.intelligence.depletion")} value={requirement.depletion_mm == null ? t("common.noData") : `${requirement.depletion_mm.toFixed(1)} mm`} />
                    <Detail label={t("fieldDetail.intelligence.effectiveRainfall")} value={requirement.effective_rainfall_mm == null ? t("common.noData") : `${requirement.effective_rainfall_mm.toFixed(1)} mm`} />
                    <Detail label={t("fieldDetail.intelligence.area")} value={requirement.area_ha == null ? "—" : `${requirement.area_ha.toFixed(2)} ha`} />
                    <Detail label={t("fieldDetail.intelligence.efficiency")} value={requirement.application_efficiency == null ? t("fieldDetail.intelligence.notSet") : `${Math.round(requirement.application_efficiency * 100)}%`} />
                  </dl>
                  {requirement.assumptions.length > 0 && (
                    <ul className="mt-3 space-y-1 text-xs text-muted-foreground">
                      {requirement.assumptions.map((assumption) => (
                        <li key={assumption} className="flex gap-2">
                          <Info className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                          <span>{assumption}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {requirement.missing_inputs.length > 0 && (
                    <p className="mt-2 text-xs text-caution-foreground">
                      {t("fieldDetail.intelligence.missingInputs")}: {requirement.missing_inputs.join(", ")}
                    </p>
                  )}
                </details>
              )}

              {prediction.limitations.length > 0 && (
                <ul className="space-y-1 text-xs text-muted-foreground">
                  {prediction.limitations.map((limitation) => (
                    <li key={limitation} className="flex gap-2">
                      <Info className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
                      <span>{limitation}</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-lg">{t("fieldDetail.intelligence.scheduleTitle")}</CardTitle>
            <CalendarClock className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            {schedule.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("schedule.emptyDescription")}</p>
            ) : (
              <IrrigationScheduleList
                entries={schedule}
                onChanged={() => {
                  load()
                  onChanged?.()
                }}
                showDate
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-lg">{t("fieldDetail.intelligence.waterTitle")}</CardTitle>
            <Layers className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent className="space-y-3">
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">{t("analytics.totalWaterUsed")}</dt>
                <dd className="text-lg font-semibold tabular-nums">{formatLitres(totalMeasured)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">{t("analytics.measuredEvents")}</dt>
                <dd className="text-lg font-semibold tabular-nums">{events.length - unmeasuredCount}</dd>
              </div>
            </dl>
            {unmeasuredCount > 0 && (
              <p className="text-xs text-muted-foreground">
                {t("analytics.unmeasuredEvents")}: {unmeasuredCount}. {t("analytics.unmeasuredNote")}
              </p>
            )}

            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("analytics.noIrrigationEvents")}</p>
            ) : (
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-input">
                      <th scope="col" className="py-1">{t("readings.history.timestamp")}</th>
                      <th scope="col" className="py-1">{t("fieldDetail.intelligence.waterApplied")}</th>
                      <th scope="col" className="py-1">{t("common.source")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events.map((event) => (
                      <tr key={event.id} className="border-b border-input/40">
                        <td className="py-1">{formatDateTime(event.start_time, i18n.language)}</td>
                        <td className="py-1">
                          {event.water_volume_litres == null ? t("schedule.notRecorded") : formatLitres(event.water_volume_litres)}
                        </td>
                        <td className="py-1">{event.application_method || t("common.source")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("fieldDetail.intelligence.predictionHistoryTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-input">
                    <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.timestamp")}</th>
                    <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.intelligence.predictedMoisture")}</th>
                    <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.intelligence.requirementMm")}</th>
                    <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.intelligence.estimatedVolume")}</th>
                    <th scope="col" className="pb-2 text-muted-foreground">{t("common.status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((row) => (
                    <tr key={row.id} className="border-b border-input/50">
                      <td className="py-2">{formatDateTime(row.predicted_at, i18n.language)}</td>
                      <td className="py-2">{row.predicted_moisture == null ? "—" : `${row.predicted_moisture.toFixed(1)}%`}</td>
                      <td className="py-2">{row.irrigation_requirement_mm == null ? "—" : `${row.irrigation_requirement_mm.toFixed(1)} mm`}</td>
                      <td className="py-2">{row.estimated_volume_litres == null ? "—" : formatLitres(row.estimated_volume_litres)}</td>
                      <td className="py-2">
                        <Badge variant={row.status === "validated" ? "healthy" : "caution"}>
                          {t(`model.status.${row.status === "validated" ? "validated" : "provisional"}`)}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("fieldDetail.intelligence.settingsTitle")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p className="text-muted-foreground">{t("fieldDetail.intelligence.settingsDescription")}</p>
          <dl className="grid gap-3 sm:grid-cols-2">
            <Detail label={t("fieldDetail.intelligence.applicationMethod")} value={settings?.application_method || t("fieldDetail.intelligence.notSet")} />
            <Detail label={t("fieldDetail.intelligence.applicationRate")} value={settings?.application_rate_litres_per_hour == null ? t("fieldDetail.intelligence.notSet") : `${formatNumber(settings.application_rate_litres_per_hour)} L/h`} />
            <Detail label={t("fieldDetail.intelligence.efficiency")} value={settings?.application_efficiency == null ? t("fieldDetail.intelligence.notSet") : `${Math.round(settings.application_efficiency * 100)}%`} />
            <Detail label={t("fieldDetail.intelligence.waterSource")} value={settings?.water_source || t("fieldDetail.intelligence.notSet")} />
          </dl>
        </CardContent>
      </Card>
    </div>
  )
}

function Metric({ label, value, icon }: { label: string; value: React.ReactNode; icon?: React.ReactNode }) {
  return (
    <div className="rounded-md border border-input p-3">
      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
        {icon}
        {label}
      </p>
      <p className="mt-1 text-lg font-semibold tabular-nums">{value}</p>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  )
}
