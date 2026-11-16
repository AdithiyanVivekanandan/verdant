"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import { AlertCircle, Droplets, FileDown, Plus } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { formatDateTime } from "@/lib/utils"
import type { Field, Reading, Sensor } from "@/lib/types"

const STAGES = [
  { value: "Seedling", key: "registerField.stages.seedling" },
  { value: "Vegetative", key: "registerField.stages.vegetative" },
  { value: "Flowering", key: "registerField.stages.flowering" },
  { value: "Fruiting / Grain formation", key: "registerField.stages.fruiting" },
  { value: "Maturity", key: "registerField.stages.maturity" },
  { value: "Harvest", key: "registerField.stages.harvest" },
]

export default function ReadingsPage() {
  const { t, i18n } = useTranslation()
  const [fields, setFields] = useState<Field[]>([])
  const [sensors, setSensors] = useState<Sensor[]>([])
  const [readings, setReadings] = useState<Reading[]>([])
  const [selectedField, setSelectedField] = useState("")
  const [sensorId, setSensorId] = useState("")
  const [growthStage, setGrowthStage] = useState("Vegetative")
  const [moisture, setMoisture] = useState("")
  const [temperature, setTemperature] = useState("")
  const [recordedAt, setRecordedAt] = useState("")
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  const loadFields = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.get<Field[]>("/api/v1/fields/")
      setFields(data)
      if (data.length > 0) {
        setSelectedField((prev) => prev || String(data[0].id))
      }
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }, [t])

  const loadSensors = useCallback(async (field: string) => {
    if (!field) { setSensors([]); setSensorId(""); return }
    try {
      const data = await api.get<Sensor[]>(`/api/v1/fields/${field}/sensors`)
      setSensors(data)
      setSensorId(data[0]?.id ? String(data[0].id) : "")
    } catch {
      setSensors([])
      setSensorId("")
    }
  }, [])

  const loadReadings = useCallback(async (field: string) => {
    try {
      const data = await api.get<Reading[]>(`/api/v1/sensors/?limit=100${field ? `&field_id=${field}` : ""}`)
      setReadings(data)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    }
  }, [t])

  useEffect(() => {
    loadFields()
    const now = new Date()
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
    setRecordedAt(now.toISOString().slice(0, 16))
  }, [loadFields])

  useEffect(() => {
    if (selectedField) {
      loadSensors(selectedField)
      loadReadings(selectedField)
    } else {
      loadReadings("")
    }
  }, [selectedField, loadSensors, loadReadings])

  useEffect(() => {
    const field = fields.find((item) => String(item.id) === selectedField)
    if (field) setGrowthStage(field.growth_stage)
  }, [fields, selectedField])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setError("")
    setSuccess("")
    const moistureValue = Number(moisture)
    const temperatureValue = temperature === "" ? null : Number(temperature)
    if (!selectedField) { setError(t("readings.validation.fieldRequired")); return }
    if (moisture === "" || Number.isNaN(moistureValue)) { setError(t("readings.validation.moistureRequired")); return }
    if (moistureValue < 0 || moistureValue > 100) { setError(t("readings.validation.moistureRange")); return }
    if (temperatureValue != null && (Number.isNaN(temperatureValue) || temperatureValue < -10 || temperatureValue > 60)) {
      setError(t("readings.validation.temperatureRange")); return
    }
    if (!recordedAt || Number.isNaN(new Date(recordedAt).getTime())) { setError(t("readings.validation.invalidDate")); return }
    setSubmitting(true)
    try {
      await api.post("/api/v1/sensors/", {
        field_id: Number(selectedField),
        sensor_id: sensorId ? Number(sensorId) : null,
        crop_growth_stage: growthStage,
        moisture_percentage: moistureValue,
        soil_temperature: temperatureValue,
        recorded_at: new Date(recordedAt).toISOString(),
      })
      setSuccess(t("readings.success"))
      setMoisture("")
      setTemperature("")
      setRecordedAt(() => {
        const now = new Date()
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset())
        return now.toISOString().slice(0, 16)
      })
      loadReadings(selectedField)
    } catch (err: any) {
      const detail = err?.body?.detail
      setError(typeof detail === "string" ? detail : Array.isArray(detail) ? detail[0]?.msg : t("errors.serverError"))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <p className="py-10 text-sm text-muted-foreground">{t("common.loading")}</p>

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("readings.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("readings.subtitle")}</p>
        </div>
        {readings.length > 0 && (
          <Button variant="outline" asChild><Link href="/reports"><FileDown className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("readings.history.exportCsv")}</Link></Button>
        )}
      </header>

      {error && <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}
      {success && <div role="status" className="rounded-lg border border-healthy/40 bg-healthy/5 p-4 text-sm">{success}</div>}

      {fields.length === 0 ? (
        <EmptyState
          icon={<Droplets className="h-8 w-8" />}
          title={t("fields.noData")}
          description={t("fields.noFieldsDescription")}
          action={<Button asChild><Link href="/fields/new">{t("fields.registerField")}</Link></Button>}
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader><CardTitle className="flex items-center gap-2 text-lg"><Plus className="h-4 w-4" aria-hidden="true" />{t("readings.sectionRecord")}</CardTitle></CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="reading-field">{t("readings.selectField")}</Label>
                  <Select id="reading-field" required value={selectedField} onChange={(event) => setSelectedField(event.target.value)} className="w-full">
                    <SelectOption value="">{t("readings.selectFieldPlaceholder")}</SelectOption>
                    {fields.map((field) => <SelectOption key={field.id} value={field.id}>{field.field_name}</SelectOption>)}
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="reading-sensor">{t("readings.sensorId")}</Label>
                  <Select id="reading-sensor" value={sensorId} onChange={(event) => setSensorId(event.target.value)} className="w-full">
                    <SelectOption value="">{t("fields.card.noSensor")}</SelectOption>
                    {sensors.map((sensor) => <SelectOption key={sensor.id} value={sensor.id}>{sensor.sensor_identifier}</SelectOption>)}
                  </Select>
                  {sensors.length === 0 && <p className="text-xs text-muted-foreground">{t("fieldDetail.noSensor")} {t("readings.manualAllowed")}</p>}
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="reading-stage">{t("readings.growthStage")}</Label>
                  <Select id="reading-stage" value={growthStage} onChange={(event) => setGrowthStage(event.target.value)} className="w-full" required>
                    {STAGES.map((stage) => <SelectOption key={stage.value} value={stage.value}>{t(stage.key)}</SelectOption>)}
                  </Select>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="reading-moisture">{t("readings.moisture")}</Label>
                  <Input id="reading-moisture" type="number" inputMode="decimal" step="0.1" min="0" max="100" required value={moisture} onChange={(event) => setMoisture(event.target.value)} placeholder={t("readings.moisturePlaceholder")} />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="reading-temperature">{t("readings.temperature")}</Label>
                  <Input id="reading-temperature" type="number" inputMode="decimal" step="0.1" value={temperature} onChange={(event) => setTemperature(event.target.value)} placeholder={t("readings.temperaturePlaceholder")} />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="reading-date">{t("readings.recordedDate")}</Label>
                    <Input id="reading-date" type="date" required value={recordedAt.split("T")[0] || ""} onChange={(event) => setRecordedAt(`${event.target.value}T${(recordedAt.split("T")[1] || "").slice(0, 5)}`)} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="reading-time">{t("readings.recordedTime")}</Label>
                    <Input id="reading-time" type="time" required value={(recordedAt.split("T")[1] || "").slice(0, 5)} onChange={(event) => setRecordedAt(`${recordedAt.split("T")[0]}T${event.target.value}`)} />
                  </div>
                </div>

                <p className="flex items-start gap-2 text-xs text-muted-foreground">
                  <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                  {t("readings.manualNotice")}
                </p>
                <Button type="submit" loading={submitting} className="w-full">{t("readings.submitReading")}</Button>
              </form>
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader className="flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <CardTitle className="text-lg">{t("readings.history.title")}</CardTitle>
              <p className="text-xs text-muted-foreground">{t("readings.history.showingLatest")}</p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-input">
                      <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.timestamp")}</th>
                      <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.field")}</th>
                      <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.sensorId")}</th>
                      <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.moisture")}</th>
                      <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.temperature")}</th>
                      <th scope="col" className="pb-2 text-muted-foreground">{t("readings.history.source")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {readings.length === 0 ? (
                      <tr><td colSpan={6} className="py-8 text-center text-muted-foreground">{t("readings.history.noReadings")}</td></tr>
                    ) : readings.map((reading) => (
                      <tr key={reading.id} className="border-b border-input/50">
                        <td className="whitespace-nowrap py-2">{formatDateTime(reading.recorded_at, i18n.language)}</td>
                        <td className="py-2">{reading.field_name || "—"}</td>
                        <td className="py-2">{reading.sensor_identifier || t("common.unknown")}</td>
                        <td className="py-2 tabular-nums">{reading.moisture_percentage}%</td>
                        <td className="py-2 tabular-nums">{reading.soil_temperature == null ? "—" : `${reading.soil_temperature}°C`}</td>
                        <td className="py-2">{t(reading.source === "manual" ? "common.sourceManual" : "common.sourceSensor")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
