"use client"

import { useTranslation } from "react-i18next"
import { AlertCircle, CloudSun, Droplets, Info, MapPin, Wind } from "lucide-react"
import { formatDateTime } from "@/lib/utils"
import type { WeatherCurrent } from "@/lib/types"

export function WeatherCurrentCard({
  weather,
  fieldName,
  onRetry,
}: {
  weather: WeatherCurrent | null
  fieldName?: string
  onRetry?: () => void
}) {
  const { t, i18n } = useTranslation()
  const available = !!weather?.available

  if (!available) {
    const reason = weather?.reason
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          <AlertCircle className="h-4 w-4 text-caution" aria-hidden="true" />
          {t("weather.unavailable")}
        </div>
        <p className="text-sm text-muted-foreground">
          {reason === "no_location" ? t("weather.noLocation") : t("weather.providerUnavailable")}
        </p>
        {reason === "no_location" && fieldName && (
          <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.addLocationFor", { field: fieldName })}
          </p>
        )}
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="rounded-md border border-input px-3 py-1.5 text-sm hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {t("common.retry")}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <p className="text-2xl font-bold tabular-nums">
            {weather?.temperature == null ? "—" : `${Math.round(weather.temperature)}°C`}
          </p>
          <p className="text-sm capitalize text-muted-foreground">
            {weather?.conditions || t("weather.conditionsNotStored")}
          </p>
        </div>
        <CloudSun className="h-7 w-7 text-muted-foreground" aria-hidden="true" />
      </div>
      <dl className="space-y-2 text-sm">
        <div className="flex items-center justify-between gap-3">
          <dt className="flex items-center gap-2 text-muted-foreground">
            <Droplets className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.humidity")}
          </dt>
          <dd>{weather?.humidity == null ? "—" : `${Math.round(weather.humidity)}%`}</dd>
        </div>
        <div className="flex items-center justify-between gap-3">
          <dt className="flex items-center gap-2 text-muted-foreground">
            <Droplets className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.rainfallProbability")}
          </dt>
          <dd>{weather?.rainfall_probability == null ? "—" : `${Math.round(weather.rainfall_probability)}%`}</dd>
        </div>
        <div className="flex items-center justify-between gap-3">
          <dt className="flex items-center gap-2 text-muted-foreground">
            <Wind className="h-3.5 w-3.5" aria-hidden="true" />
            {t("weather.wind")}
          </dt>
          <dd>{weather?.wind_speed == null ? "—" : `${Math.round(weather.wind_speed)} km/h`}</dd>
        </div>
      </dl>
      <div className="flex items-start gap-1.5 border-t border-input pt-2 text-xs text-muted-foreground">
        {weather?.cached ? (
          <>
            <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-caution" aria-hidden="true" />
            <span>
              {t("weather.cached")} · {weather?.recorded_at ? formatDateTime(weather.recorded_at, i18n.language) : ""}
            </span>
          </>
        ) : (
          <>
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span>{t("weather.sourceOpenweathermap")}</span>
          </>
        )}
      </div>
    </div>
  )
}
