"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import { CloudSun, Droplets, MapPin, Wind } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectOption } from "@/components/ui/select"
import { EmptyState } from "@/components/ui/empty-state"
import { WeatherCurrentCard } from "@/components/weather/weather-current"
import { formatDate } from "@/lib/utils"
import type { Field, WeatherCurrent, WeatherForecast } from "@/lib/types"

export default function WeatherPage() {
  const { t, i18n } = useTranslation()
  const [fields, setFields] = useState<Field[]>([])
  const [selectedField, setSelectedField] = useState("")
  const [weather, setWeather] = useState<WeatherCurrent | null>(null)
  const [forecast, setForecast] = useState<WeatherForecast | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    api.get<Field[]>("/api/v1/fields/")
      .then((data) => {
        setFields(data)
        const queryField = Number(new URLSearchParams(window.location.search).get("field"))
        if (queryField && data.some((field) => field.id === queryField)) setSelectedField(String(queryField))
        else if (data.length === 1) setSelectedField(String(data[0].id))
      })
      .catch((err: any) => setError(err.message || t("errors.networkError")))
  }, [])

  useEffect(() => {
    if (selectedField) loadWeather()
  }, [selectedField])

  async function loadWeather() {
    setLoading(true)
    setError("")
    setWeather(null)
    setForecast(null)
    try {
      const [current, days] = await Promise.all([
        api.get<WeatherCurrent>(`/api/v1/weather/current/${selectedField}`),
        api.get<WeatherForecast>(`/api/v1/weather/forecast/${selectedField}`).catch(() => null),
      ])
      setWeather(current)
      setForecast(days)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }

  const field = fields.find((item) => String(item.id) === selectedField)
  const forecastDays = forecast?.available ? forecast.forecast : []

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">{t("weather.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("weather.subtitle")}</p>
      </header>

      {fields.length === 0 ? (
        <EmptyState
          icon={<CloudSun className="h-8 w-8" />}
          title={t("fields.noData")}
          description={t("fields.noFieldsDescription")}
          action={<Button asChild><Link href="/fields/new">{t("fields.registerField")}</Link></Button>}
        />
      ) : (
        <>
          <Card>
            <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-end">
              <div className="w-full sm:max-w-sm">
                <label htmlFor="weather-field" className="mb-1.5 block text-sm font-medium">{t("weather.selectField")}</label>
                <Select id="weather-field" value={selectedField} onChange={(event) => setSelectedField(event.target.value)} className="w-full">
                  <SelectOption value="">{t("weather.selectField")}</SelectOption>
                  {fields.map((item) => <SelectOption key={item.id} value={item.id}>{item.field_name}</SelectOption>)}
                </Select>
              </div>
              {field && (
                <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
                  {field.village || field.location}
                </p>
              )}
            </CardContent>
          </Card>

          {error && <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}

          {loading && <p className="text-sm text-muted-foreground">{t("common.loading")}</p>}

          {!loading && !selectedField && <EmptyState title={t("weather.selectField")} />}

          {!loading && selectedField && weather && (
            <div className="grid gap-4 lg:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><CloudSun className="h-5 w-5" aria-hidden="true" />{t("weather.current")}</CardTitle></CardHeader>
                <CardContent>
                  <WeatherCurrentCard weather={weather} fieldName={field?.field_name} onRetry={loadWeather} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><Droplets className="h-5 w-5" aria-hidden="true" />{t("weather.forecast")}</CardTitle></CardHeader>
                <CardContent>
                  {!forecast?.available ? (
                    <div className="space-y-2 text-sm text-muted-foreground">
                      <p>{t("weather.forecastUnavailable")}</p>
                      {forecast?.reason === "no_location" && <p>{t("weather.noLocation")}</p>}
                    </div>
                  ) : forecastDays.length === 0 ? (
                    <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
                  ) : (
                    <ul className="space-y-3">
                      {forecastDays.map((day) => (
                        <li key={day.date} className="grid grid-cols-2 gap-2 rounded-md border border-input p-3 text-sm sm:grid-cols-4">
                          <span className="font-medium">{formatDate(day.date, i18n.language)}</span>
                          <span className="capitalize text-muted-foreground">{day.conditions || t("common.unknown")}</span>
                          <span className="tabular-nums">{Math.round(day.temperature)}°C</span>
                          <span className="flex items-center gap-1 tabular-nums text-muted-foreground"><Droplets className="h-3.5 w-3.5" aria-hidden="true" />{Math.round(day.rainfall_probability)}%</span>
                          <span className="flex items-center gap-1 text-xs text-muted-foreground"><Wind className="h-3.5 w-3.5" aria-hidden="true" />{Math.round(day.wind_speed)} km/h</span>
                          <span className="col-span-2 text-xs text-muted-foreground sm:col-span-3">
                            {t("weather.humidity")}: {Math.round(day.humidity)}%
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          <p className="text-xs text-muted-foreground">
            {t("weather.footnote")}
          </p>
        </>
      )}
    </div>
  )
}
