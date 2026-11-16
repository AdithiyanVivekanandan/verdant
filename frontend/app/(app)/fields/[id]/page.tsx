"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { useTranslation } from "react-i18next"
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  Clock,
  Droplets,
  Edit,
  MapPin,
  Plus,
  Radio,
  Sprout,
  Thermometer,
  Trash2,
} from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { EmptyState } from "@/components/ui/empty-state"
import { FreshnessBadge, StatusBadge } from "@/components/fields/status-badge"
import { FieldIntelligencePanel } from "@/components/fields/field-intelligence-panel"
import { GuidancePanel } from "@/components/guidance/guidance-panel"
import { WeatherCurrentCard } from "@/components/weather/weather-current"
import { ResponsiveLineChart } from "@/components/dashboard/moisture-chart"
import { ageLabel } from "@/lib/status"
import { formatDateTime } from "@/lib/utils"
import type { Field, FieldSummary, Guidance, Reading, Sensor, WeatherCurrent } from "@/lib/types"

const SENSOR_TYPES = ["Soil Moisture", "Soil Moisture + Temperature", "Multi-parameter"]

export default function FieldDetailPage() {
  const { t, i18n } = useTranslation()
  const router = useRouter()
  const params = useParams()
  const id = Number(params.id)
  const [field, setField] = useState<Field | null>(null)
  const [summary, setSummary] = useState<FieldSummary | null>(null)
  const [guidance, setGuidance] = useState<Guidance | null>(null)
  const [sensors, setSensors] = useState<Sensor[]>([])
  const [readings, setReadings] = useState<Reading[]>([])
  const [weather, setWeather] = useState<WeatherCurrent | null>(null)
  const [range, setRange] = useState<"24h" | "7d" | "30d">("7d")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [created, setCreated] = useState(false)
  const [sensorForm, setSensorForm] = useState({ sensor_identifier: "", sensor_type: SENSOR_TYPES[0], installation_date: "" })
  const [sensorSaving, setSensorSaving] = useState(false)
  const [sensorMessage, setSensorMessage] = useState("")
  const [sensorError, setSensorError] = useState("")

  useEffect(() => {
    setCreated(new URLSearchParams(window.location.search).get("created") === "1")
  }, [])

  useEffect(() => {
    loadAll()
  }, [id, range])

  async function loadAll() {
    setLoading(true)
    setError("")
    try {
      const now = new Date()
      const start = new Date(now)
      if (range === "24h") start.setDate(start.getDate() - 1)
      else if (range === "7d") start.setDate(start.getDate() - 7)
      else start.setDate(start.getDate() - 30)
      const [f, summaries, g, s, r, w] = await Promise.all([
        api.get<Field>(`/api/v1/fields/${id}`),
        api.get<FieldSummary[]>("/api/v1/dashboard/fields").catch(() => []),
        api.get<Guidance>(`/api/v1/guidance/${id}`).catch(() => null),
        api.get<Sensor[]>(`/api/v1/fields/${id}/sensors`).catch(() => []),
        api.get<Reading[]>(`/api/v1/sensors/?field_id=${id}&start_date=${start.toISOString()}&end_date=${now.toISOString()}&limit=200`).catch(() => []),
        api.get<WeatherCurrent>(`/api/v1/weather/current/${id}`).catch(() => null),
      ])
      setField(f)
      setSummary(summaries.find((item) => item.id === id) || null)
      setGuidance(g)
      setSensors(s)
      setReadings(r)
      setWeather(w)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete() {
    setDeleting(true)
    try {
      await api.del(`/api/v1/fields/${id}`)
      router.push("/fields?deleted=1")
    } catch (err: any) {
      setError(err.message || t("errors.somethingWentWrong"))
      setDeleting(false)
    }
  }

  async function addSensor(event: React.FormEvent) {
    event.preventDefault()
    setSensorSaving(true)
    setSensorError("")
    setSensorMessage("")
    try {
      const sensor = await api.post<Sensor>(`/api/v1/fields/${id}/sensors`, {
        sensor_identifier: sensorForm.sensor_identifier.trim(),
        sensor_type: sensorForm.sensor_type,
        installation_date: sensorForm.installation_date || null,
      })
      setSensors((current) => [...current, sensor])
      setSensorForm({ sensor_identifier: "", sensor_type: SENSOR_TYPES[0], installation_date: "" })
      setSensorMessage(t("fieldDetail.sensorAdded"))
      loadAll()
    } catch (err: any) {
      setSensorError(typeof err?.body?.detail === "string" ? err.body.detail : t("errors.somethingWentWrong"))
    } finally {
      setSensorSaving(false)
    }
  }

  const latest = readings[0] || null
  const locale = i18n.language

  if (loading) {
    return <div className="py-10 text-sm text-muted-foreground">{t("common.loading")}</div>
  }

  if (!field) {
    return (
      <EmptyState
        title={t("errors.notFound")}
        action={<Button asChild><Link href="/fields">{t("fieldDetail.backToFields")}</Link></Button>}
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <Link href="/fields" className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          {t("fieldDetail.backToFields")}
        </Link>
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">{field.field_name}</h1>
              {summary && <StatusBadge status={summary.status} />}
            </div>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>{field.crop_type}</span><span aria-hidden="true">·</span>
              <span>{field.area_acres} {t("common.acres")}</span><span aria-hidden="true">·</span>
              <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" aria-hidden="true" />{field.village || field.location}</span>
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/fields/${id}/edit`}><Edit className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("fieldDetail.editField")}</Link>
            </Button>
            <Button variant="ghost" size="sm" className="text-destructive" onClick={() => setDeleteOpen(true)}>
              <Trash2 className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("fieldDetail.deleteField")}
            </Button>
          </div>
        </div>
      </div>

      {created && (
        <div role="status" className="flex items-start gap-2 rounded-lg border border-healthy/40 bg-healthy/5 p-3 text-sm">
          <CheckCircle2 className="mt-0.5 h-4 w-4 text-healthy" aria-hidden="true" />
          {t("registerField.created")}
        </div>
      )}
      {error && <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("fieldDetail.currentMoisture")}</p>
            <p className="mt-1 text-3xl font-bold tabular-nums">{latest ? `${latest.moisture_percentage}%` : "—"}</p>
            {summary && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5">
                <FreshnessBadge freshness={summary.freshness} />
                <span className="text-xs text-muted-foreground">
                  {summary.age_hours == null ? t("freshness.missing") : ageLabel(t, summary.age_hours)}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("fieldDetail.latestTemperature")}</p>
            <p className="mt-1 text-3xl font-bold tabular-nums">{latest?.soil_temperature == null ? "—" : `${latest.soil_temperature}°C`}</p>
            <p className="mt-2 text-xs text-muted-foreground">{latest ? formatDateTime(latest.recorded_at, locale) : t("common.noData")}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-muted-foreground">{t("guidance.targetBand")}</p>
            <p className="mt-1 text-3xl font-bold tabular-nums">
              {summary?.threshold_low == null || summary.threshold_high == null ? "—" : `${summary.threshold_low}–${summary.threshold_high}%`}
            </p>
            <p className="mt-2 text-xs text-muted-foreground">{summary?.crop_band ? t("fieldDetail.cropBand") : t("fieldDetail.generalBand")}</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">{t("fieldDetail.guidanceTitle")}</CardTitle></CardHeader>
        <CardContent>
          {guidance ? (
            <GuidancePanel guidance={guidance} headingLevel={3} />
          ) : (
            <p className="flex items-start gap-2 text-sm text-muted-foreground">
              <AlertCircle className="mt-0.5 h-4 w-4" aria-hidden="true" />
              {t("guidance.unavailable")}
            </p>
          )}
        </CardContent>
      </Card>

      <section aria-labelledby="field-intelligence-heading" className="space-y-3">
        <h2 id="field-intelligence-heading" className="text-lg font-semibold">
          {t("fieldDetail.intelligence.title")}
        </h2>
        <FieldIntelligencePanel fieldId={id} fieldName={field.field_name} onChanged={loadAll} />
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-lg">{t("fieldDetail.chart.title")}</CardTitle>
            <div className="flex gap-1" role="group" aria-label={t("fieldDetail.chart.rangeLabel")}>
              {(["24h", "7d", "30d"] as const).map((value) => (
                <Button key={value} variant={range === value ? "secondary" : "ghost"} size="sm" onClick={() => setRange(value)} aria-pressed={range === value}>
                  {t(`fieldDetail.chart.${value === "24h" ? "hours24" : value === "7d" ? "days7" : "days30"}`)}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            {readings.length === 0 ? (
              <EmptyState
                icon={<Droplets className="h-8 w-8" />}
                title={t("fieldDetail.noReadings")}
                description={t("fieldDetail.noReadingsDescription")}
                action={<Button asChild><Link href="/readings">{t("dashboard.addReading")}</Link></Button>}
              />
            ) : (
              <ResponsiveLineChart readings={readings} field={field} thresholdLow={summary?.threshold_low} thresholdHigh={summary?.threshold_high} />
            )}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-lg">{t("fieldDetail.sensorHealth")}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {sensors.length === 0 ? (
                <p className="text-sm text-muted-foreground">{t("fieldDetail.noSensor")}</p>
              ) : (
                <ul className="space-y-2">
                  {sensors.map((sensor) => (
                    <li key={sensor.id} className="rounded-md border border-input p-3">
                      <p className="flex items-center gap-2 text-sm font-medium"><Radio className="h-4 w-4 text-muted-foreground" aria-hidden="true" />{sensor.sensor_identifier}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{sensor.sensor_type}</p>
                    </li>
                  ))}
                </ul>
              )}
              <dl className="space-y-2 border-t border-input pt-3 text-sm">
                <div className="flex justify-between gap-3"><dt className="text-muted-foreground">{t("fieldDetail.lastReading")}</dt><dd>{summary?.last_updated ? formatDateTime(summary.last_updated, locale) : t("freshness.missing")}</dd></div>
                <div className="flex justify-between gap-3"><dt className="text-muted-foreground">{t("fieldDetail.dataFreshness")}</dt><dd>{summary ? <FreshnessBadge freshness={summary.freshness} /> : "—"}</dd></div>
                <div className="flex justify-between gap-3"><dt className="text-muted-foreground">{t("common.source")}</dt><dd>{latest ? t(latest.source === "manual" ? "common.sourceManual" : "common.sourceSensor") : "—"}</dd></div>
                <div className="flex justify-between gap-3"><dt className="text-muted-foreground">{t("fieldDetail.validation")}</dt><dd>{latest?.validation_status || "—"}</dd></div>
                <div className="flex justify-between gap-3"><dt className="text-muted-foreground">{t("fieldDetail.ingestedAt")}</dt><dd>{latest ? formatDateTime(latest.ingested_at, locale) : "—"}</dd></div>
              </dl>
              {sensors.length > 0 && summary?.status === "sensor_unavailable" && (
                <p className="flex items-start gap-2 rounded-md border border-caution/40 bg-caution/10 p-3 text-xs">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  {t("fieldDetail.sensorNoReadings")}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-lg">{t("dashboard.weather.title")}</CardTitle></CardHeader>
            <CardContent>
              <WeatherCurrentCard weather={weather} fieldName={field.field_name} />
              <Link href={`/weather?field=${id}`} className="mt-3 inline-block text-sm text-primary hover:underline">{t("weather.viewForecast")}</Link>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-lg">{t("fieldDetail.addSensor")}</CardTitle></CardHeader>
        <CardContent>
          {sensorMessage && <p className="mb-3 rounded-md border border-healthy/40 bg-healthy/5 p-2 text-sm">{sensorMessage}</p>}
          {sensorError && <p role="alert" className="mb-3 rounded-md border border-destructive/40 bg-destructive/5 p-2 text-sm text-destructive">{sensorError}</p>}
          <form onSubmit={addSensor} className="grid gap-3 sm:grid-cols-4 sm:items-end">
            <div className="space-y-1.5">
              <Label htmlFor="new-sensor-id">{t("registerField.sensorId")}</Label>
              <Input id="new-sensor-id" required value={sensorForm.sensor_identifier} onChange={(event) => setSensorForm({ ...sensorForm, sensor_identifier: event.target.value })} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new-sensor-type">{t("registerField.sensorType")}</Label>
              <Select id="new-sensor-type" value={sensorForm.sensor_type} onChange={(event) => setSensorForm({ ...sensorForm, sensor_type: event.target.value })}>
                {SENSOR_TYPES.map((type) => <SelectOption key={type} value={type}>{type}</SelectOption>)}
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new-sensor-date">{t("registerField.installationDate")}</Label>
              <Input id="new-sensor-date" type="date" value={sensorForm.installation_date} onChange={(event) => setSensorForm({ ...sensorForm, installation_date: event.target.value })} />
            </div>
            <Button type="submit" loading={sensorSaving}><Plus className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("fieldDetail.addSensorButton")}</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-lg">{t("fieldDetail.historyTable.title")}</CardTitle></CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-input">
                  <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.historyTable.timestamp")}</th>
                  <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.historyTable.moisture")}</th>
                  <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.historyTable.temperature")}</th>
                  <th scope="col" className="pb-2 text-muted-foreground">{t("common.source")}</th>
                  <th scope="col" className="pb-2 text-muted-foreground">{t("fieldDetail.growthStage")}</th>
                </tr>
              </thead>
              <tbody>
                {readings.length === 0 ? (
                  <tr><td colSpan={5} className="py-6 text-center text-muted-foreground">{t("fieldDetail.historyTable.noReadings")}</td></tr>
                ) : readings.map((reading) => (
                  <tr key={reading.id} className="border-b border-input/50">
                    <td className="py-2">{formatDateTime(reading.recorded_at, locale)}</td>
                    <td className="py-2">{reading.moisture_percentage}%</td>
                    <td className="py-2">{reading.soil_temperature == null ? "—" : `${reading.soil_temperature}°C`}</td>
                    <td className="py-2">{t(reading.source === "manual" ? "common.sourceManual" : "common.sourceSensor")}</td>
                    <td className="py-2">{reading.growth_stage}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-lg">{t("fieldDetail.detailsTitle")}</CardTitle></CardHeader>
        <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
          <Detail icon={<MapPin className="h-4 w-4" aria-hidden="true" />} label={t("fieldDetail.location")} value={field.location} />
          <Detail icon={<MapPin className="h-4 w-4" aria-hidden="true" />} label={t("fieldDetail.villageDistrict")} value={[field.village, field.district, field.state].filter(Boolean).join(", ") || "—"} />
          <Detail icon={<Clock className="h-4 w-4" aria-hidden="true" />} label={t("fieldDetail.sowingDate")} value={field.sowing_date ? formatDateTime(field.sowing_date, locale) : "—"} />
          <Detail icon={<Sprout className="h-4 w-4" aria-hidden="true" />} label={t("fieldDetail.growthStage")} value={field.growth_stage} />
          <Detail icon={<Thermometer className="h-4 w-4" aria-hidden="true" />} label={t("fieldDetail.soilType")} value={field.soil_type} />
          <Detail icon={<Droplets className="h-4 w-4" aria-hidden="true" />} label={t("settings.areaUnit")} value={`${field.area_acres} ${t("common.acres")}`} />
        </CardContent>
      </Card>

      {deleteOpen && (
        <Dialog role="alertdialog" aria-modal="true" aria-labelledby="delete-title">
          <DialogContent>
            <DialogHeader>
              <DialogTitle id="delete-title">{t("fieldDetail.deleteTitle")}</DialogTitle>
              <DialogDescription>{t("fieldDetail.deleteConfirm")}</DialogDescription>
            </DialogHeader>
            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeleteOpen(false)}>{t("common.cancel")}</Button>
              <Button variant="destructive" loading={deleting} onClick={handleDelete}>{t("common.delete")}</Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

function Detail({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2 border-b border-input/60 pb-2">
      <span className="mt-0.5 text-muted-foreground">{icon}</span>
      <div><dt className="text-xs text-muted-foreground">{label}</dt><dd className="font-medium">{value}</dd></div>
    </div>
  )
}
