"use client"

import { useCallback, useEffect, useState } from "react"
import Link from "next/link"
import { useTranslation } from "react-i18next"
import { CalendarClock, Info, Sprout } from "lucide-react"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { IrrigationScheduleList } from "@/components/analytics/irrigation-schedule-list"
import { formatLitres } from "@/components/analytics/water-charts"
import type { Guidance, TodaySchedule } from "@/lib/types"

/**
 * Irrigation guidance and today's schedule.
 *
 * The schedule is generated on demand from the recorded data, then reused
 * for the day so the farmer never sees a duplicate entry.
 */
export default function GuidancePage() {
  const { t } = useTranslation()
  const [schedule, setSchedule] = useState<TodaySchedule | null>(null)
  const [guidance, setGuidance] = useState<Guidance[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const [s, g] = await Promise.all([
        api.get<TodaySchedule>("/api/v1/irrigation/schedule/today"),
        api.get<Guidance[]>("/api/v1/guidance/").catch(() => []),
      ])
      setSchedule(s)
      setGuidance(g)
    } catch (err: any) {
      setError(err.message || t("errors.networkError"))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    load()
  }, [load])

  const entries = schedule?.entries || []
  const needsWater = entries.filter(
    (entry) => entry.priority === "critical" || entry.priority === "high" || entry.priority === "medium"
  )
  const canWait = entries.filter((entry) => entry.priority === "low")
  const uncertain = entries.filter((entry) => entry.priority === "uncertain")

  return (
    <div className="space-y-6">
      <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("schedule.title")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("guidance.subtitle")}</p>
        </div>
        {schedule && (
          <p className="text-sm text-muted-foreground">
            {schedule.date} · {schedule.timezone}
          </p>
        )}
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-destructive bg-destructive/5 p-4 text-sm text-destructive">
          {error}
          <button type="button" onClick={load} className="ml-2 underline">
            {t("common.retry")}
          </button>
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <>
          <Card>
            <CardContent className="space-y-3 pt-4">
              <p className="flex items-start gap-2 rounded-md border border-info/30 bg-info/5 p-3 text-xs text-muted-foreground">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-info" aria-hidden="true" />
                {schedule?.decision_support_notice || t("schedule.decisionSupportNotice")}
              </p>
              <dl className="grid grid-cols-3 gap-3 text-sm">
                <div>
                  <dt className="text-xs text-muted-foreground">{t("schedule.needsIrrigation")}</dt>
                  <dd className="text-lg font-semibold tabular-nums">{needsWater.length}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t("schedule.canWait")}</dt>
                  <dd className="text-lg font-semibold tabular-nums">{canWait.length}</dd>
                </div>
                <div>
                  <dt className="text-xs text-muted-foreground">{t("schedule.uncertain")}</dt>
                  <dd className="text-lg font-semibold tabular-nums">{uncertain.length}</dd>
                </div>
              </dl>
              <p className="text-sm">
                <span className="text-muted-foreground">{t("schedule.totalEstimatedToday")}: </span>
                <span className="font-semibold tabular-nums">{formatLitres(schedule?.total_estimated_litres ?? 0)}</span>
              </p>
            </CardContent>
          </Card>

          <section aria-labelledby="needs-water-heading" className="space-y-3">
            <h2 id="needs-water-heading" className="text-lg font-semibold">{t("schedule.needsIrrigation")}</h2>
            <IrrigationScheduleList
              entries={needsWater}
              onChanged={load}
              emptyTitle={t("schedule.emptyTitle")}
              emptyDescription={t("schedule.emptyDescription")}
              showDate
            />
          </section>

          {uncertain.length > 0 && (
            <section aria-labelledby="uncertain-heading" className="space-y-3">
              <h2 id="uncertain-heading" className="text-lg font-semibold">{t("schedule.uncertain")}</h2>
              <IrrigationScheduleList entries={uncertain} onChanged={load} showDate />
            </section>
          )}

          {canWait.length > 0 && (
            <section aria-labelledby="can-wait-heading" className="space-y-3">
              <h2 id="can-wait-heading" className="text-lg font-semibold">{t("schedule.canWait")}</h2>
              <IrrigationScheduleList entries={canWait} onChanged={load} showDate />
            </section>
          )}

          <section aria-labelledby="field-guidance-heading" className="space-y-3">
            <h2 id="field-guidance-heading" className="text-lg font-semibold">{t("guidance.title")}</h2>
            {guidance.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("common.noData")}</p>
            ) : (
              <ul className="grid gap-3 sm:grid-cols-2">
                {guidance.map((item) => (
                  <li key={item.field_id} className="rounded-md border border-input p-3">
                    <p className="flex flex-wrap items-center gap-2 font-medium">
                      <Sprout className="h-4 w-4 text-primary" aria-hidden="true" />
                      <Link href={`/fields/${item.field_id}`} className="hover:underline">
                        {item.field_name}
                      </Link>
                      <Badge variant={item.status === "critical" ? "destructive" : item.status === "healthy" ? "healthy" : "caution"}>
                        {t(`status.${item.status}`)}
                      </Badge>
                    </p>
                    <p className="mt-1 text-sm text-muted-foreground">{item.headline}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{item.explanation}</p>
                    <p className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                      <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
                      {t(`guidance.reason_${item.reason}`, { defaultValue: item.reason })}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <Button variant="outline" asChild className="w-full sm:w-auto">
            <Link href="/fields">{t("dashboard.viewAllFields")}</Link>
          </Button>
        </>
      )}
    </div>
  )
}
