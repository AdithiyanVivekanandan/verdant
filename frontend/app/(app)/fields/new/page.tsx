"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useTranslation } from "react-i18next"
import { Barcode, CheckCircle2, ChevronLeft, Leaf, MapPin, Sprout } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Card, CardContent } from "@/components/ui/card"
import { api } from "@/lib/api"
import type { Field, Profile } from "@/lib/types"

const CROPS = [
  { value: "Rice", label: "registerField.crops.rice" },
  { value: "Wheat", label: "registerField.crops.wheat" },
  { value: "Maize", label: "registerField.crops.maize" },
  { value: "Cotton", label: "registerField.crops.cotton" },
  { value: "Sugarcane", label: "registerField.crops.sugarcane" },
  { value: "Tomato", label: "registerField.crops.tomato" },
  { value: "Ragi", label: "registerField.crops.ragi" },
  { value: "Other", label: "registerField.crops.other" },
]

const SOILS = [
  { value: "Red soil", label: "registerField.soils.red" },
  { value: "Black soil", label: "registerField.soils.black" },
  { value: "Loamy soil", label: "registerField.soils.loamy" },
  { value: "Sandy soil", label: "registerField.soils.sandy" },
  { value: "Clay soil", label: "registerField.soils.clay" },
  { value: "Other", label: "registerField.soils.other" },
]

const STAGES = [
  { value: "Seedling", label: "registerField.stages.seedling" },
  { value: "Vegetative", label: "registerField.stages.vegetative" },
  { value: "Flowering", label: "registerField.stages.flowering" },
  { value: "Fruiting / Grain formation", label: "registerField.stages.fruiting" },
  { value: "Maturity", label: "registerField.stages.maturity" },
  { value: "Harvest", label: "registerField.stages.harvest" },
]

const SENSOR_TYPES = [
  { value: "Soil Moisture", label: "registerField.sensorTypes.moisture" },
  { value: "Soil Moisture + Temperature", label: "registerField.sensorTypes.moistureTemperature" },
  { value: "Multi-parameter", label: "registerField.sensorTypes.multiparameter" },
]

function apiError(err: any, fallback: string): string {
  const detail = err?.body?.detail
  if (typeof detail === "string") return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return err?.message || fallback
}

export default function RegisterFieldPage() {
  const { t } = useTranslation()
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [created, setCreated] = useState<Field | null>(null)
  const [sensorWarning, setSensorWarning] = useState("")
  const [sensorAdded, setSensorAdded] = useState(false)

  const [form, setForm] = useState({
    field_name: "",
    farmer_name: "",
    location: "",
    village: "",
    district: "",
    state: "",
    latitude: "",
    longitude: "",
    area_acres: "",
    crop_type: "Rice",
    soil_type: "Loamy soil",
    growth_stage: "Seedling",
    sowing_date: "",
    sensor_identifier: "",
    sensor_type: "Soil Moisture",
    installation_date: "",
  })

  useEffect(() => {
    api.get<Profile>("/api/v1/auth/me")
      .then((profile) => setForm((current) => ({ ...current, farmer_name: current.farmer_name || profile.full_name })))
      .catch(() => undefined)
  }, [])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError("")
    setSensorWarning("")
    setLoading(true)
    try {
      const field = await api.post<Field>("/api/v1/fields/", {
        field_name: form.field_name,
        farmer_name: form.farmer_name,
        location: form.location,
        village: form.village || null,
        district: form.district || null,
        state: form.state || null,
        latitude: form.latitude ? parseFloat(form.latitude) : null,
        longitude: form.longitude ? parseFloat(form.longitude) : null,
        area_acres: parseFloat(form.area_acres),
        crop_type: form.crop_type,
        soil_type: form.soil_type,
        growth_stage: form.growth_stage,
        sowing_date: form.sowing_date || null,
      })
      setCreated(field)
      if (form.sensor_identifier.trim()) {
        try {
          await api.post(`/api/v1/fields/${field.id}/sensors`, {
            sensor_identifier: form.sensor_identifier.trim(),
            sensor_type: form.sensor_type,
            installation_date: form.installation_date || null,
          })
          setSensorAdded(true)
        } catch (sensorError: any) {
          setSensorWarning(apiError(sensorError, t("registerField.sensorSaveFailed")))
        }
      }
    } catch (err: any) {
      setError(apiError(err, t("errors.serverError")))
    } finally {
      setLoading(false)
    }
  }

  if (created) {
    return (
      <div className="mx-auto max-w-xl space-y-4">
        <Card>
          <CardContent className="space-y-4 p-6 text-center">
            <CheckCircle2 className="mx-auto h-10 w-10 text-healthy" aria-hidden="true" />
            <h1 className="text-2xl font-bold">{t("registerField.confirmationTitle")}</h1>
            <p className="text-sm text-muted-foreground">
              {t("registerField.confirmationBody", { field: created.field_name })}
            </p>
            {form.sensor_identifier.trim() && (
              <p className={`rounded-md border p-3 text-sm ${sensorAdded ? "border-healthy/40 bg-healthy/5" : "border-caution/40 bg-caution/10"}`}>
                {sensorAdded ? t("registerField.sensorAdded", { sensor: form.sensor_identifier.trim() }) : sensorWarning}
              </p>
            )}
            <div className="flex flex-col justify-center gap-2 sm:flex-row">
              <Button onClick={() => router.push(`/fields/${created.id}?created=1`)}>{t("registerField.openField")}</Button>
              <Button variant="outline" onClick={() => router.push("/readings")}>{t("registerField.addFirstReading")}</Button>
              <Button variant="ghost" onClick={() => router.push("/fields/new")}>{t("registerField.addAnother")}</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <button
          type="button"
          onClick={() => router.push("/fields")}
          className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          {t("fieldDetail.backToFields")}
        </button>
        <h1 className="text-2xl font-bold tracking-tight">{t("registerField.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("registerField.subtitle")}</p>
      </div>

      {error && <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <Section icon={<MapPin className="h-5 w-5" />} title={t("registerField.sectionIdentification")}>
          <p className="text-xs text-muted-foreground">{t("registerField.requiredHint")}</p>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={t("registerField.fieldName")} id="field_name" value={form.field_name} onChange={(v) => setForm({ ...form, field_name: v })} placeholder={t("registerField.fieldNamePlaceholder")} required />
            <Field label={t("registerField.farmerName")} id="farmer_name" value={form.farmer_name} onChange={(v) => setForm({ ...form, farmer_name: v })} required />
          </div>
          <Field label={t("registerField.location")} id="location" value={form.location} onChange={(v) => setForm({ ...form, location: v })} required hint={t("registerField.locationHint")} />
          <div className="grid gap-4 md:grid-cols-3">
            <Field label={t("registerField.village")} id="village" value={form.village} onChange={(v) => setForm({ ...form, village: v })} optional />
            <Field label={t("registerField.district")} id="district" value={form.district} onChange={(v) => setForm({ ...form, district: v })} optional />
            <Field label={t("registerField.state")} id="state" value={form.state} onChange={(v) => setForm({ ...form, state: v })} optional />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={t("registerField.latitude")} id="latitude" type="number" step="any" value={form.latitude} onChange={(v) => setForm({ ...form, latitude: v })} optional hint={t("registerField.coordinatesHint")} />
            <Field label={t("registerField.longitude")} id="longitude" type="number" step="any" value={form.longitude} onChange={(v) => setForm({ ...form, longitude: v })} optional />
          </div>
        </Section>

        <Section icon={<Leaf className="h-5 w-5" />} title={t("registerField.sectionAgriculture")}>
          <div className="grid gap-4 md:grid-cols-3">
            <FieldSelect label={t("registerField.cropType")} id="crop_type" value={form.crop_type} onChange={(v) => setForm({ ...form, crop_type: v })} options={CROPS} />
            <FieldSelect label={t("registerField.soilType")} id="soil_type" value={form.soil_type} onChange={(v) => setForm({ ...form, soil_type: v })} options={SOILS} />
            <FieldSelect label={t("registerField.growthStage")} id="growth_stage" value={form.growth_stage} onChange={(v) => setForm({ ...form, growth_stage: v })} options={STAGES} />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label={t("registerField.areaAcres")} id="area_acres" type="number" step="0.01" min="0.01" value={form.area_acres} onChange={(v) => setForm({ ...form, area_acres: v })} required />
            <Field label={t("registerField.sowingDate")} id="sowing_date" type="date" value={form.sowing_date} onChange={(v) => setForm({ ...form, sowing_date: v })} />
          </div>
        </Section>

        <Section icon={<Barcode className="h-5 w-5" />} title={t("registerField.sectionSensor")}>
          <p className="text-xs text-muted-foreground">{t("registerField.sensorOptionalHint")}</p>
          <div className="grid gap-4 md:grid-cols-3">
            <Field label={t("registerField.sensorId")} id="sensor_identifier" value={form.sensor_identifier} onChange={(v) => setForm({ ...form, sensor_identifier: v })} optional hint={t("registerField.sensorIdHint")} />
            <FieldSelect label={t("registerField.sensorType")} id="sensor_type" value={form.sensor_type} onChange={(v) => setForm({ ...form, sensor_type: v })} options={SENSOR_TYPES} />
            <Field label={t("registerField.installationDate")} id="installation_date" type="date" value={form.installation_date} onChange={(v) => setForm({ ...form, installation_date: v })} optional />
          </div>
        </Section>

        <div className="flex flex-col-reverse justify-end gap-3 pt-2 sm:flex-row">
          <Button type="button" variant="outline" onClick={() => router.push("/fields")}>{t("common.cancel")}</Button>
          <Button type="submit" loading={loading}>
            <Sprout className="mr-1.5 h-4 w-4" aria-hidden="true" />
            {t("registerField.registerField")}
          </Button>
        </div>
      </form>
    </div>
  )
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4 rounded-lg border border-input bg-card p-4 sm:p-6">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-primary">{icon}</div>
        <h2 className="font-semibold">{title}</h2>
      </div>
      <Separator />
      {children}
    </section>
  )
}

function Field({ label, id, value, onChange, type = "text", placeholder, required, optional, step, min, hint }: { label: string; id: string; value: string; onChange: (val: string) => void; type?: string; placeholder?: string; required?: boolean; optional?: boolean; step?: string; min?: string; hint?: string }) {
  const { t } = useTranslation()
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>
        {label} {optional && <span className="font-normal text-muted-foreground">({t("common.optional")})</span>}
      </Label>
      <Input id={id} type={type} step={step} min={min} required={required} placeholder={placeholder} value={value} onChange={(event) => onChange(event.target.value)} className="w-full" />
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

function FieldSelect({ label, id, value, onChange, options }: { label: string; id: string; value: string; onChange: (val: string) => void; options: { value: string; label: string }[] }) {
  const { t } = useTranslation()
  return (
    <div className="space-y-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Select id={id} value={value} onChange={(event) => onChange(event.target.value)} className="w-full">
        {options.map((option) => <SelectOption key={option.value} value={option.value}>{t(option.label)}</SelectOption>)}
      </Select>
    </div>
  )
}
