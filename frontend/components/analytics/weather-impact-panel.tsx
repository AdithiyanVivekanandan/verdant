"use client"

import { useMemo } from "react"
import { useTranslation } from "react-i18next"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { CloudRain, Thermometer, Wind } from "lucide-react"
import { formatDateTime } from "@/lib/utils"
import type { WeatherCurrent, WeatherForecast } from "@/lib/types"

const AXIS_STYLE = { fontSize: 11, fill: "rgb(var(--muted-foreground))" }
const TOOLTIP_STYLE = {
  background: "rgb(var(--card))",
  border: "1px solid var(--input)",
  borderRadius: 6,
  fontSize: 12,
}

/**
 * Weather impact panel.
 *
 * Only metrics that the provider actually supplied are shown. When the
 * provider returned nothing, the panel says so instead of filling the
 * space with placeholders.
 */
export function WeatherImpactPanel({
  current,
  forecast,
}: {
  current: WeatherCurrent | null
  forecast: WeatherForecast | null
}) {
  const { t, i18n } = useTranslation()

  const forecastData = useMemo(
    () =>
      (forecast?.forecast || []).map((day) => ({
        ...day,
        label: new Date(day.date).toLocaleDateString(
          i18n.language === "en" ? "en-US" : i18n.language,
          { weekday: "short" }
        ),
      })),
    [forecast, i18n.language]
  )

  if (!current || !current.available) {
    return (
      <div className="rounded-md border border-dashed border-input p-4 text-sm text-muted-foreground">
        <p className="font-medium text-foreground">{t("weather.unavailable")}</p>
        <p className="mt-1">
          {current?.message || t("weather.unavailableShort")}
        </p>
      </div>
    )
  }

  const hasTemperature = typeof current.temperature === "number"
  const hasRainfallForecast = forecastData.some((day) => typeof day.rainfall_probability === "number")

  return (
    <div className="space-y-4">
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="rounded-md border border-input p-3">
          <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Thermometer className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.temperature")}
          </dt>
          <dd className="mt-1 text-lg font-semibold tabular-nums">
            {hasTemperature ? `${current.temperature}°C` : "—"}
          </dd>
        </div>
        <div className="rounded-md border border-input p-3">
          <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <CloudRain className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.rainProbability")}
          </dt>
          <dd className="mt-1 text-lg font-semibold tabular-nums">
            {current.rainfall_probability == null ? "—" : `${current.rainfall_probability}%`}
          </dd>
        </div>
        <div className="rounded-md border border-input p-3">
          <dt className="text-xs text-muted-foreground">{t("weather.humidity")}</dt>
          <dd className="mt-1 text-lg font-semibold tabular-nums">
            {current.humidity == null ? "—" : `${current.humidity}%`}
          </dd>
        </div>
        <div className="rounded-md border border-input p-3">
          <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Wind className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.wind")}
          </dt>
          <dd className="mt-1 text-lg font-semibold tabular-nums">
            {current.wind_speed == null ? "—" : `${current.wind_speed} m/s`}
          </dd>
        </div>
      </dl>

      {forecastData.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="mb-1 text-sm font-medium">{t("weather.forecastTemperature")}</p>
            <div style={{ height: 170 }} role="img" aria-label={t("weather.forecastTemperature")}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastData} margin={{ top: 8, right: 12, bottom: 0, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
                  <XAxis dataKey="label" tick={AXIS_STYLE} />
                  <YAxis tick={AXIS_STYLE} width={40} />
                  <Tooltip
                    formatter={(value: any, name: any) => [
                      `${value == null ? "—" : Number(value).toFixed(1)}°C`,
                      name === "temperature"
                        ? t("weather.temperature")
                        : name === "max_temperature"
                          ? t("weather.max")
                          : t("weather.min"),
                    ]}
                    contentStyle={TOOLTIP_STYLE}
                  />
                  <Line type="monotone" dataKey="max_temperature" stroke="rgb(var(--caution))" strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
                  <Line type="monotone" dataKey="min_temperature" stroke="rgb(var(--info))" strokeWidth={2} dot={{ r: 2 }} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {hasRainfallForecast && (
            <div>
              <p className="mb-1 text-sm font-medium">{t("weather.rainProbability")}</p>
              <div style={{ height: 170 }} role="img" aria-label={t("weather.rainProbability")}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={forecastData} margin={{ top: 8, right: 12, bottom: 0, left: -20 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
                    <XAxis dataKey="label" tick={AXIS_STYLE} />
                    <YAxis domain={[0, 100]} tick={AXIS_STYLE} width={40} />
                    <Tooltip
                      formatter={(value: any) => [`${value == null ? "—" : Number(value)}%`, t("weather.rainProbability")]}
                      contentStyle={TOOLTIP_STYLE}
                    />
                    <Bar dataKey="rainfall_probability" radius={[4, 4, 0, 0]} isAnimationActive={false}>
                      {forecastData.map((day, index) => (
                        <Cell
                          key={day.date}
                          fill={Number(day.rainfall_probability) >= 60 ? "rgb(var(--info))" : "rgb(var(--accent))"}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        {t("weather.retrievedAt")}:{" "}
        {current.recorded_at ? formatDateTime(current.recorded_at, i18n.language) : "—"}
        {current.source ? ` · ${current.source}` : ""}
      </p>
    </div>
  )
}
