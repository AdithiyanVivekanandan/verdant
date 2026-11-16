"use client"

import { useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import {
  CalendarClock,
  CheckCircle2,
  Droplets,
  Loader2,
  SkipForward,
  Timer,
} from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { EmptyState } from "@/components/ui/empty-state"
import { formatNumber } from "@/lib/utils"
import { formatLitres } from "@/components/analytics/water-charts"
import type { IrrigationSchedule } from "@/lib/types"

const PRIORITY_TONE: Record<string, string> = {
  critical: "bg-destructive/10 text-destructive border-destructive/30",
  high: "bg-caution/15 text-caution-foreground border-caution/40",
  medium: "bg-secondary/10 text-secondary border-secondary/30",
  low: "bg-muted text-muted-foreground border-border",
  uncertain: "bg-muted text-muted-foreground border-border",
}

const STATUS_TONE: Record<string, string> = {
  pending: "bg-muted text-muted-foreground border-border",
  accepted: "bg-info/10 text-info border-info/30",
  completed: "bg-healthy/10 text-healthy border-healthy/30",
  skipped: "bg-muted text-muted-foreground border-border",
  cancelled: "bg-muted text-muted-foreground border-border",
}

export function PriorityBadge({ priority }: { priority: string }) {
  const { t } = useTranslation()
  return (
    <Badge className={PRIORITY_TONE[priority] || PRIORITY_TONE.low}>
      {t(`schedule.priority.${priority}`)}
    </Badge>
  )
}

export function ScheduleStatusBadge({ status }: { status: string }) {
  const { t } = useTranslation()
  return (
    <Badge className={STATUS_TONE[status] || STATUS_TONE.pending}>
      {t(`schedule.status.${status}`)}
    </Badge>
  )
}

/**
 * A farmer-facing list of today's irrigation recommendations.
 *
 * Every entry explains why the field is prioritised, and the farmer can
 * accept, skip or complete it. The list never claims to control irrigation
 * equipment.
 */
export function IrrigationScheduleList({
  entries,
  onChanged,
  emptyTitle,
  emptyDescription,
  showDate = false,
}: {
  entries: IrrigationSchedule[]
  onChanged?: () => void
  emptyTitle?: string
  emptyDescription?: string
  showDate?: boolean
}) {
  const { t } = useTranslation()
  const [busyId, setBusyId] = useState<number | null>(null)
  const [error, setError] = useState("")
  const [completingId, setCompletingId] = useState<number | null>(null)
  const [volumeDraft, setVolumeDraft] = useState<Record<number, string>>({})
  const [durationDraft, setDurationDraft] = useState<Record<number, string>>({})

  if (entries.length === 0) {
    return (
      <EmptyState
        icon={<CalendarClock className="h-9 w-9" />}
        title={emptyTitle || t("schedule.emptyTitle")}
        description={emptyDescription || t("schedule.emptyDescription")}
      />
    )
  }

  async function run(action: () => Promise<unknown>) {
    setError("")
    try {
      await action()
      onChanged?.()
    } catch (err: any) {
      setError(typeof err?.body?.detail === "string" ? err.body.detail : t("errors.somethingWentWrong"))
    }
  }

  async function accept(entry: IrrigationSchedule) {
    setBusyId(entry.id)
    await run(() => api.post(`/api/v1/irrigation/schedule/${entry.id}/accept`))
    setBusyId(null)
  }

  async function skip(entry: IrrigationSchedule) {
    setBusyId(entry.id)
    await run(() => api.post(`/api/v1/irrigation/schedule/${entry.id}/skip`, { reason: t("schedule.skippedByFarmer") }))
    setBusyId(null)
  }

  async function complete(entry: IrrigationSchedule) {
    setBusyId(entry.id)
    const rawVolume = volumeDraft[entry.id]
    const rawDuration = durationDraft[entry.id]
    await run(() =>
      api.post(`/api/v1/irrigation/schedule/${entry.id}/complete`, {
        actual_volume_litres: rawVolume === undefined || rawVolume === "" ? null : Number(rawVolume),
        actual_duration_minutes: rawDuration === undefined || rawDuration === "" ? null : Number(rawDuration),
      })
    )
    setBusyId(null)
    setCompletingId(null)
  }

  return (
    <div className="space-y-3">
      {error && (
        <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <ul className="space-y-3">
        {entries.map((entry) => {
          const busy = busyId === entry.id
          const isCompleting = completingId === entry.id
          const actionable = entry.status === "pending" || entry.status === "accepted"
          return (
            <li
              key={entry.id}
              className="rounded-md border border-input p-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="flex flex-wrap items-center gap-2 font-medium">
                    <Link href={`/fields/${entry.field_id}`} className="hover:underline">
                      {entry.field_name || `#${entry.field_id}`}
                    </Link>
                    <PriorityBadge priority={entry.priority} />
                    <ScheduleStatusBadge status={entry.status} />
                    {showDate && <span className="text-xs text-muted-foreground">{entry.scheduled_date}</span>}
                  </p>
                  {entry.reason && (
                    <p className="mt-1 text-sm text-muted-foreground">{entry.reason}</p>
                  )}
                </div>
                <div className="text-right text-sm">
                  <p className="font-semibold tabular-nums">
                    {entry.estimated_volume_litres == null
                      ? t("schedule.noVolumeEstimate")
                      : formatLitres(entry.estimated_volume_litres)}
                  </p>
                  {entry.estimated_duration_minutes != null && (
                    <p className="text-xs text-muted-foreground">
                      <Timer className="mr-1 inline h-3 w-3" aria-hidden="true" />
                      {formatNumber(entry.estimated_duration_minutes)} {t("common.minutes")}
                    </p>
                  )}
                  {entry.recommended_start_time && (
                    <p className="text-xs text-muted-foreground">
                      <CalendarClock className="mr-1 inline h-3 w-3" aria-hidden="true" />
                      {entry.recommended_start_time}
                      {entry.recommended_window_end ? `–${entry.recommended_window_end}` : ""}
                    </p>
                  )}
                </div>
              </div>

              {entry.confidence != null && (
                <p className="mt-2 text-xs text-muted-foreground">
                  {t("schedule.confidence")}: {Math.round(entry.confidence * 100)}%
                  {entry.model_version ? ` · ${t("schedule.source")}: ${entry.model_version}` : ""}
                </p>
              )}

              {entry.status === "completed" && (
                <p className="mt-2 flex items-center gap-1.5 text-xs text-healthy">
                  <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
                  {t("schedule.actualWater")}:{" "}
                  {entry.actual_volume_litres == null
                    ? t("schedule.notRecorded")
                    : formatLitres(entry.actual_volume_litres)}
                  {entry.estimated_volume_litres != null && entry.actual_volume_litres != null && (
                    <span className="text-muted-foreground">
                      ({t("schedule.planned")}: {formatLitres(entry.estimated_volume_litres)})
                    </span>
                  )}
                </p>
              )}

              {actionable && (
                <div className="mt-3 space-y-3 border-t border-input/70 pt-3">
                  {isCompleting ? (
                    <div className="grid gap-2 sm:grid-cols-2">
                      <div className="space-y-1">
                        <Label htmlFor={`volume-${entry.id}`}>{t("schedule.actualVolume")}</Label>
                        <Input
                          id={`volume-${entry.id}`}
                          type="number"
                          min={0}
                          inputMode="decimal"
                          placeholder={t("schedule.volumePlaceholder")}
                          value={volumeDraft[entry.id] ?? ""}
                          onChange={(event) =>
                            setVolumeDraft((current) => ({ ...current, [entry.id]: event.target.value }))
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor={`duration-${entry.id}`}>{t("schedule.actualDuration")}</Label>
                        <Input
                          id={`duration-${entry.id}`}
                          type="number"
                          min={0}
                          inputMode="numeric"
                          placeholder={t("schedule.durationPlaceholder")}
                          value={durationDraft[entry.id] ?? ""}
                          onChange={(event) =>
                            setDurationDraft((current) => ({ ...current, [entry.id]: event.target.value }))
                          }
                        />
                      </div>
                      <div className="flex gap-2 sm:col-span-2">
                        <Button size="sm" loading={busy} onClick={() => complete(entry)}>
                          <Droplets className="mr-1.5 h-4 w-4" aria-hidden="true" />
                          {t("schedule.saveActual")}
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setCompletingId(null)}>
                          {t("common.cancel")}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {entry.status === "pending" && (
                        <Button size="sm" variant="outline" loading={busy} onClick={() => accept(entry)}>
                          <CheckCircle2 className="mr-1.5 h-4 w-4" aria-hidden="true" />
                          {t("schedule.accept")}
                        </Button>
                      )}
                      <Button size="sm" variant="outline" loading={busy} onClick={() => setCompletingId(entry.id)}>
                        <Droplets className="mr-1.5 h-4 w-4" aria-hidden="true" />
                        {t("schedule.recordActual")}
                      </Button>
                      <Button size="sm" variant="ghost" loading={busy} onClick={() => skip(entry)}>
                        <SkipForward className="mr-1.5 h-4 w-4" aria-hidden="true" />
                        {t("schedule.skip")}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </li>
          )
        })}
      </ul>

      {busyId !== null && (
        <p className="flex items-center gap-2 text-xs text-muted-foreground" role="status">
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
          {t("common.saving")}
        </p>
      )}
    </div>
  )
}
