"use client"

import { useTranslation } from "react-i18next"
import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { formatDateTime } from "@/lib/utils"

export function ResponsiveLineChart({
  readings,
  field,
  thresholdLow,
  thresholdHigh,
}: {
  readings: any[]
  field: any
  thresholdLow?: number | null
  thresholdHigh?: number | null
}) {
  const { t, i18n } = useTranslation()
  const data = readings
    .slice()
    .reverse()
    .map((reading) => ({
      time: reading.recorded_at ? formatDateTime(reading.recorded_at, i18n.language) : "",
      moisture: reading.moisture_percentage == null ? null : Number(reading.moisture_percentage),
    }))

  return (
    <figure className="space-y-2">
      <figcaption className="text-sm text-muted-foreground">
        {t("fieldDetail.chart.subtitle")}
        {thresholdLow != null && thresholdHigh != null && (
          <span className="ml-1">
            · {t("guidance.targetBand")}: {thresholdLow}–{thresholdHigh}%
          </span>
        )}
      </figcaption>
      <div className="h-64 w-full" role="img" aria-label={t("fieldDetail.chart.ariaLabel", { field: field?.field_name || "" })}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
            <XAxis dataKey="time" tick={{ fontSize: 11, fill: "rgb(var(--muted-foreground))" }} minTickGap={24} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "rgb(var(--muted-foreground))" }} />
            <Tooltip
              formatter={(value: any) => [value == null ? "—" : `${Number(value).toFixed(1)}%`, t("common.moisture")]}
              contentStyle={{ background: "rgb(var(--card))", border: "1px solid var(--input)", borderRadius: 6, fontSize: 12 }}
            />
            {thresholdLow != null && (
              <ReferenceLine y={thresholdLow} stroke="rgb(var(--caution))" strokeDasharray="4 4" label={{ value: t("chart.lowBand"), position: "insideBottomLeft", fontSize: 10, fill: "rgb(var(--caution-foreground))" }} />
            )}
            {thresholdHigh != null && (
              <ReferenceLine y={thresholdHigh} stroke="rgb(var(--caution))" strokeDasharray="4 4" label={{ value: t("chart.highBand"), position: "insideTopLeft", fontSize: 10, fill: "rgb(var(--caution-foreground))" }} />
            )}
            <Line type="monotone" dataKey="moisture" stroke="rgb(var(--primary))" strokeWidth={2} dot={false} connectNulls={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <table className="sr-only">
        <caption>{t("fieldDetail.chart.tableCaption", { field: field?.field_name || "" })}</caption>
        <thead>
          <tr><th scope="col">{t("readings.history.timestamp")}</th><th scope="col">{t("readings.history.moisture")}</th></tr>
        </thead>
        <tbody>
          {data.map((point, index) => (
            <tr key={`${point.time}-${index}`}><td>{point.time}</td><td>{point.moisture == null ? "—" : `${point.moisture}%`}</td></tr>
          ))}
        </tbody>
      </table>
    </figure>
  )
}
