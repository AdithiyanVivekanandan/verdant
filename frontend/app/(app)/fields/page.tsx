"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import { Map, Plus, Search } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectOption } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { FieldCard } from "@/components/fields/field-card"
import { STATUS_ORDER, isAttention } from "@/lib/status"
import type { FieldSummary } from "@/lib/types"

export default function FieldsPage() {
  const { t } = useTranslation()
  const [fields, setFields] = useState<FieldSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("all")

  useEffect(() => {
    loadFields()
  }, [])

  async function loadFields() {
    setLoading(true)
    setError("")
    try {
      const data = await api.get<FieldSummary[]>("/api/v1/dashboard/fields")
      setFields(data)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    return fields
      .filter((field) => status === "all" || field.status === status)
      .filter((field) => !query || field.field_name.toLowerCase().includes(query) || field.crop_type.toLowerCase().includes(query))
      .sort((a, b) => Number(isAttention(b.status)) - Number(isAttention(a.status)))
  }, [fields, search, status])

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("fields.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("fields.subtitle")}</p>
        </div>
        <Button asChild>
          <Link href="/fields/new"><Plus className="mr-1.5 h-4 w-4" aria-hidden="true" />{t("fields.registerField")}</Link>
        </Button>
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">
          {error}
          <button type="button" onClick={loadFields} className="ml-2 underline">{t("common.retry")}</button>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" aria-hidden="true" />
          <label htmlFor="field-search" className="sr-only">{t("fields.search")}</label>
          <Input
            id="field-search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("fields.search")}
            className="pl-9"
          />
        </div>
        <div className="sm:w-56">
          <label htmlFor="status-filter" className="sr-only">{t("common.status")}</label>
          <Select id="status-filter" value={status} onChange={(event) => setStatus(event.target.value)} className="w-full">
            <SelectOption value="all">{t("fields.allStatuses")}</SelectOption>
            {STATUS_ORDER.map((value) => (
              <SelectOption key={value} value={value}>{t(`status.${value}`)}</SelectOption>
            ))}
          </Select>
        </div>
      </div>

      <p className="text-xs text-muted-foreground" role="status">
        {t("fields.showingCount", { count: filtered.length, total: fields.length })}
      </p>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[1, 2, 3, 4].map((i) => <Card key={i} className="p-4"><Skeleton className="h-36 w-full" /></Card>)}
        </div>
      ) : fields.length === 0 ? (
        <EmptyState
          icon={<Map className="h-10 w-10" />}
          title={t("fields.noData")}
          description={t("fields.noFieldsDescription")}
          action={<Button asChild><Link href="/fields/new">{t("fields.registerField")}</Link></Button>}
        />
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<Search className="h-8 w-8" />}
          title={t("fields.empty")}
          action={<Button variant="outline" onClick={() => { setSearch(""); setStatus("all") }}>{t("fields.clearFilters")}</Button>}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((field) => <FieldCard key={field.id} field={field} />)}
        </div>
      )}
    </div>
  )
}
