"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useParams, useRouter } from "next/navigation"
import { useTranslation } from "react-i18next"
import { ArrowLeft } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectOption } from "@/components/ui/select"
import type { Field } from "@/lib/types"

const CROPS = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Tomato", "Ragi", "Other"]
const SOILS = ["Red soil", "Black soil", "Loamy soil", "Sandy soil", "Clay soil", "Other"]
const STAGES = [
  { value: "Seedling", key: "registerField.stages.seedling" },
  { value: "Vegetative", key: "registerField.stages.vegetative" },
  { value: "Flowering", key: "registerField.stages.flowering" },
  { value: "Fruiting / Grain formation", key: "registerField.stages.fruiting" },
  { value: "Maturity", key: "registerField.stages.maturity" },
  { value: "Harvest", key: "registerField.stages.harvest" },
]

export default function EditFieldPage() {
  const { t } = useTranslation()
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [field, setField] = useState<Field | null>(null)
  const [form, setForm] = useState({
    field_name: "", farmer_name: "", village: "", district: "", state: "",
    latitude: "", longitude: "", area_acres: "", crop_type: "Rice",
    soil_type: "Loamy soil", growth_stage: "Vegetative", sowing_date: "",
  })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    api.get<Field>(`/api/v1/fields/${id}`)
      .then((data) => {
        setField(data)
        setForm({
          field_name: data.field_name,
          farmer_name: data.farmer_name,
          village: data.village || "",
          district: data.district || "",
          state: data.state || "",
          latitude: data.latitude == null ? "" : String(data.latitude),
          longitude: data.longitude == null ? "" : String(data.longitude),
          area_acres: String(data.area_acres),
          crop_type: data.crop_type,
          soil_type: data.soil_type,
          growth_stage: data.growth_stage,
          sowing_date: data.sowing_date ? data.sowing_date.slice(0, 10) : "",
        })
      })
      .catch((err: any) => setError(err.message || t("errors.networkError")))
      .finally(() => setLoading(false))
  }, [id])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError("")
    try {
      await api.put(`/api/v1/fields/${id}`, {
        field_name: form.field_name.trim(),
        farmer_name: form.farmer_name.trim(),
        village: form.village.trim() || null,
        district: form.district.trim() || null,
        state: form.state.trim() || null,
        latitude: form.latitude === "" ? null : Number(form.latitude),
        longitude: form.longitude === "" ? null : Number(form.longitude),
        area_acres: Number(form.area_acres),
        crop_type: form.crop_type,
        soil_type: form.soil_type,
        growth_stage: form.growth_stage,
        sowing_date: form.sowing_date ? new Date(`${form.sowing_date}T00:00:00`).toISOString() : null,
      })
      router.push(`/fields/${id}`)
    } catch (err: any) {
      const detail = err?.body?.detail
      setError(typeof detail === "string" ? detail : Array.isArray(detail) ? detail[0]?.msg : t("errors.serverError"))
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <p className="py-10 text-sm text-muted-foreground">{t("common.loading")}</p>
  if (error && !field) return <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Button variant="ghost" asChild className="-ml-2">
        <Link href={`/fields/${id}`}><ArrowLeft className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("fieldDetail.backToFields")}</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-bold tracking-tight">{t("fieldDetail.editField")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{field?.field_name}</p>
      </header>
      {error && <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader><CardTitle className="text-lg">{t("registerField.sectionIdentification")}</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5"><Label htmlFor="field_name">{t("registerField.fieldName")}</Label><Input id="field_name" required value={form.field_name} onChange={(event) => setForm({ ...form, field_name: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="farmer_name">{t("registerField.farmerName")}</Label><Input id="farmer_name" required value={form.farmer_name} onChange={(event) => setForm({ ...form, farmer_name: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="village">{t("registerField.village")}</Label><Input id="village" value={form.village} onChange={(event) => setForm({ ...form, village: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="district">{t("registerField.district")}</Label><Input id="district" value={form.district} onChange={(event) => setForm({ ...form, district: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="state">{t("registerField.state")}</Label><Input id="state" value={form.state} onChange={(event) => setForm({ ...form, state: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="area_acres">{t("registerField.areaAcres")}</Label><Input id="area_acres" type="number" inputMode="decimal" step="0.01" min="0.01" required value={form.area_acres} onChange={(event) => setForm({ ...form, area_acres: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="latitude">{t("registerField.latitude")}</Label><Input id="latitude" type="number" inputMode="decimal" step="any" min="-90" max="90" value={form.latitude} onChange={(event) => setForm({ ...form, latitude: event.target.value })} /></div>
            <div className="space-y-1.5"><Label htmlFor="longitude">{t("registerField.longitude")}</Label><Input id="longitude" type="number" inputMode="decimal" step="any" min="-180" max="180" value={form.longitude} onChange={(event) => setForm({ ...form, longitude: event.target.value })} /></div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-lg">{t("registerField.sectionAgriculture")}</CardTitle></CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5"><Label htmlFor="crop_type">{t("registerField.cropType")}</Label><Select id="crop_type" value={form.crop_type} onChange={(event) => setForm({ ...form, crop_type: event.target.value })}>{CROPS.map((crop) => <SelectOption key={crop} value={crop}>{crop}</SelectOption>)}</Select></div>
            <div className="space-y-1.5"><Label htmlFor="soil_type">{t("registerField.soilType")}</Label><Select id="soil_type" value={form.soil_type} onChange={(event) => setForm({ ...form, soil_type: event.target.value })}>{SOILS.map((soil) => <SelectOption key={soil} value={soil}>{soil}</SelectOption>)}</Select></div>
            <div className="space-y-1.5"><Label htmlFor="growth_stage">{t("registerField.growthStage")}</Label><Select id="growth_stage" value={form.growth_stage} onChange={(event) => setForm({ ...form, growth_stage: event.target.value })}>{STAGES.map((stage) => <SelectOption key={stage.value} value={stage.value}>{t(stage.key)}</SelectOption>)}</Select></div>
            <div className="space-y-1.5"><Label htmlFor="sowing_date">{t("registerField.sowingDate")}</Label><Input id="sowing_date" type="date" value={form.sowing_date} onChange={(event) => setForm({ ...form, sowing_date: event.target.value })} /></div>
          </CardContent>
        </Card>

        <div className="flex flex-wrap gap-3">
          <Button type="submit" loading={saving}>{t("common.save")}</Button>
          <Button type="button" variant="outline" asChild><Link href={`/fields/${id}`}>{t("common.cancel")}</Link></Button>
        </div>
      </form>
    </div>
  )
}
