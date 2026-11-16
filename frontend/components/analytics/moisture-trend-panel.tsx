"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { CalendarRange, Droplets } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { MoistureTrendChart } from "@/components/analytics/water-charts"
import { formatDateTime } from "@/lib/utils"
import type { FieldSummary, Reading } from "@/lib/types"

type RangeKey = "24h" | "7d" | "30d" | "custom"

const RANGE_DAYS: Record<Exclude<RangeKey, "custom">, number> = {
  "24h": 1,
  "7d": 7,
  "30d": 30,
}

/**
 * Interactive soil moisture trend with a field selector and a time range.
 *
 * Missing readings are returned by the API as gaps and are drawn as gaps:
 * the chart never interpolates a missing measurement.
 */
export function MoistureTrendPanel({ fields }: { fields: FieldSummary[] }) {
  const { t, i18n } = useTranslation()
  const [fieldId, setFieldId] = useState<string>("")
  const [range, setRange] = useState<RangeKey>("7d")
  const [customStart, setCustomStart] = useState("")
  const [customEnd, setCustomEnd] = useState("")
  const [readings, setReadings] = useState<Reading[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const selected = useMemo(
    () => fields.find((field) => String(field.id) === fieldId) || fields[0] || null,
    [fields, fieldId]
  )

  const load = useCallback(async () => {
    if (!selected) {
      setReadings([])
      return
    }
    setLoading(true)
    setError("")
    try {
      const now = new Date()
      let start = new Date(now)
      if (range === "custom") {
        if (!customStart || !customEnd) {
          setReadings([])
          setLoading(false)
          return
        }
        start = new Date(customStart)
      } else {
        start.setDate(start.getDate() - RANGE_DAYS[range])
      }
      const data = await api.get<Reading[]>(
        `/api/v1/sensors/?field_id=${selected.id}&start_date=${start.toISOString()}&end_date=${now.toISOString()}&limit=500`
      )
      setReadings(data)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
      setReadings([])
    } finally {
      setLoading(false)
    }
  }, [selected, range, customStart, customEnd, t])

  useEffect(() => {
    load()
  }, [load])

  const chartData = useMemo(
    () =>
      readings
        .slice()
        .reverse()
        .map((reading) => ({
          time: reading.recorded_at ? formatDateTime(reading.recorded_at, i18n.language) : "",
          moisture: reading.moisture_percentage == null ? null : Number(reading.moisture_percentage),
        })),
    [readings, i18n.language]
  )

  return (
    <Card>
      <CardHeader className="flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle className="text-lg">{t("analytics.moistureTrends")}</CardTitle>
          <Select
            value={selected ? String(selected.id) : ""}
            onChange={(event) => setFieldId(event.target.value)}
            className="w-48"
            aria-label={t("analytics.selectField")}
          >
            {fields.map((field) => (
              <SelectOption key={field.id} value={String(field.id)}>
                {field.field_name}
              </SelectOption>
            ))}
          </Select>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex gap-1" role="group" aria-label={t("analytics.rangeLabel")}>
            {(["24h", "7d", "30d"] as const).map((value) => (
              <Button
                key={value}
                variant={range === value ? "secondary" : "ghost"}
                size="sm"
                aria-pressed={range === value}
                onClick={() => setRange(value)}
              >
                {t(`fieldDetail.chart.${value === "24h" ? "hours24" : value === "7d" ? "days7" : "days30"}`)}
              </Button>
            ))}
            <Button
              variant={range === "custom" ? "secondary" : "ghost"}
              size="sm"
              aria-pressed={range === "custom"}
              onClick={() => setRange("custom")}
            >
              <CalendarRange className="mr-1.5 h-4 w-4" aria-hidden="true" />
              {t("analytics.customRange")}
            </Button>
          </div>

          {range === "custom" && (
            <div className="flex flex-wrap items-end gap-2">
              <div className="space-y-1">
                <Label htmlFor="moisture-start" className="text-xs">
                  {t("analytics.from")}
                </Label>
                <Input
                  id="moisture-start"
                  type="date"
                  value={customStart}
                  onChange={(event) => setCustomStart(event.target.value)}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="moisture-end" className="text-xs">
                  {t("analytics.to")}
                </Label>
                <Input
                  id="moisture-end"
                  type="date"
                  value={customEnd}
                  onChange={(event) => setCustomEnd(event.target.value)}
                />
              </div>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {error && (
          <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        {selected && (
          <p className="text-sm text-muted-foreground">
            {t("analytics.bandFor")}: {selected.threshold_low ?? "—"}–{selected.threshold_high ?? "—"}% ·{" "}
            {t("analytics.readingsShown")}: {readings.length}
          </p>
        )}

        {loading ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <MoistureTrendChart
            data={chartData}
            bandLow={selected?.threshold_low ?? null}
            bandHigh={selected?.threshold_high ?? null}
            label={selected ? t("analytics.moistureTrendFor", { field: selected.field_name }) : undefined}
          />
        )}

        {selected && chartData.length > 0 && (
          <details className="rounded-md border border-input p-3 text-sm">
            <summary className="cursor-pointer font-medium">
              {t("analytics.showDataTable")}
            </summary>
            <div className="mt-2 max-h-64 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-input">
                    <th scope="col" className="py-1">{t("readings.history.timestamp")}</th>
                    <th scope="col" className="py-1">{t("readings.history.moisture")}</th>
                    <th scope="col" className="py-1">{t("common.source")}</th>
                  </tr>
                </thead>
                <tbody>
                  {chartData.map((point, index) => (
                    <tr key={`${point.time}-${index}`} className="border-b border-input/40">
                      <td className="py-1">{point.time}</td>
                      <td className="py-1">{point.moisture == null ? "—" : `${point.moisture}%`}</td>
                      <td className="py-1">{t("common.source")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        )}

        <p className="flex items-start gap-2 text-xs text-muted-foreground">
          <Droplets className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          {t("analytics.gapNotice")}
        </p>
      </CardContent>
    </Card>
  )
}
