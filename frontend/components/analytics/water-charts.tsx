"use client"

import { useMemo } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { useTranslation } from "react-i18next"
import { formatNumber } from "@/lib/utils"
import type { PlannedVsActualPoint, WaterSeriesPoint, WaterUsageByCrop, WaterUsageByField } from "@/lib/types"

const AXIS_STYLE = { fontSize: 11, fill: "rgb(var(--muted-foreground))" }
const TOOLTIP_STYLE = {
  background: "rgb(var(--card))",
  border: "1px solid var(--input)",
  borderRadius: 6,
  fontSize: 12,
}

const CROP_COLORS = [
  "rgb(var(--primary))",
  "rgb(var(--secondary))",
  "rgb(var(--healthy))",
  "rgb(var(--info))",
  "rgb(var(--caution))",
  "rgb(var(--accent))",
]

/** Formats a litre value for axes and tooltips. */
export function formatLitres(value: number | null | undefined, locale = "en"): string {
  if (value == null || Number.isNaN(value)) return "—"
  const number = Number(value)
  if (Math.abs(number) >= 1_000_000) return `${(number / 1_000_000).toFixed(2)} ML`
  if (Math.abs(number) >= 1_000) return `${(number / 1_000).toFixed(1)} kL`
  return `${formatNumber(Math.round(number), locale)} L`
}

/**
 * Daily / weekly / monthly water consumption.
 *
 * Renders nothing but an empty-state message when there is no measured
 * data: Verdant never draws a chart from invented values.
 */
export function WaterConsumptionChart({
  data,
  granularity = "day",
  height = 240,
}: {
  data: WaterSeriesPoint[]
  granularity?: "day" | "week" | "month"
  height?: number
}) {
  const { t, i18n } = useTranslation()

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        ...point,
        label:
          granularity === "month"
            ? point.bucket
            : new Date(point.bucket).toLocaleDateString(i18n.language === "en" ? "en-US" : i18n.language, {
                month: "short",
                day: "numeric",
              }),
      })),
    [data, granularity, i18n.language]
  )

  if (chartData.length === 0) {
    return (
      <div
        className="flex h-40 items-center justify-center rounded-md border border-dashed border-input text-center text-sm text-muted-foreground"
        role="status"
      >
        {t("analytics.noMeasuredWater")}
      </div>
    )
  }

  return (
    <div style={{ height }} role="img" aria-label={t("analytics.dailyConsumptionChartLabel")}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
          <XAxis dataKey="label" tick={AXIS_STYLE} minTickGap={16} />
          <YAxis tick={AXIS_STYLE} tickFormatter={(value) => formatLitres(value, i18n.language)} width={68} />
          <Tooltip
            formatter={(value: any) => [formatLitres(value == null ? null : Number(value), i18n.language), t("analytics.waterUsed")]}
            labelFormatter={(label: any) => String(label)}
            contentStyle={TOOLTIP_STYLE}
          />
          <Bar dataKey="litres" fill="rgb(var(--primary))" radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Water usage per field, as a horizontal bar chart. */
export function FieldWaterUsageChart({
  data,
  height = 260,
}: {
  data: WaterUsageByField[]
  height?: number
}) {
  const { t, i18n } = useTranslation()

  const chartData = useMemo(
    () =>
      data.map((item) => ({
        ...item,
        name: item.field_name || `#${item.field_id}`,
      })),
    [data]
  )

  if (chartData.length === 0) {
    return (
      <div
        className="flex h-40 items-center justify-center rounded-md border border-dashed border-input text-center text-sm text-muted-foreground"
        role="status"
      >
        {t("analytics.noMeasuredWater")}
      </div>
    )
  }

  return (
    <div style={{ height }} role="img" aria-label={t("analytics.fieldUsageChartLabel")}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} className="text-muted-foreground/20" />
          <XAxis type="number" tick={AXIS_STYLE} tickFormatter={(value) => formatLitres(value, i18n.language)} />
          <YAxis type="category" dataKey="name" tick={AXIS_STYLE} width={110} />
          <Tooltip
            formatter={(value: any) => [formatLitres(value == null ? null : Number(value), i18n.language), t("analytics.waterUsed")]}
            contentStyle={TOOLTIP_STYLE}
          />
          <Bar dataKey="total_litres" fill="rgb(var(--secondary))" radius={[0, 4, 4, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Water usage per crop, as a bar chart. */
export function CropWaterUsageChart({
  data,
  height = 220,
}: {
  data: WaterUsageByCrop[]
  height?: number
}) {
  const { t, i18n } = useTranslation()

  if (data.length === 0) {
    return (
      <div
        className="flex h-40 items-center justify-center rounded-md border border-dashed border-input text-center text-sm text-muted-foreground"
        role="status"
      >
        {t("analytics.noMeasuredWater")}
      </div>
    )
  }

  return (
    <div style={{ height }} role="img" aria-label={t("analytics.cropUsageChartLabel")}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
          <XAxis dataKey="crop_type" tick={AXIS_STYLE} />
          <YAxis tick={AXIS_STYLE} tickFormatter={(value) => formatLitres(value, i18n.language)} width={68} />
          <Tooltip
            formatter={(value: any) => [formatLitres(value == null ? null : Number(value), i18n.language), t("analytics.waterUsed")]}
            contentStyle={TOOLTIP_STYLE}
          />
          <Bar dataKey="total_litres" radius={[4, 4, 0, 0]} isAnimationActive={false}>
            {data.map((entry, index) => (
              <Cell key={entry.crop_type} fill={CROP_COLORS[index % CROP_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Planned (scheduled) against actual (measured) irrigation volume. */
export function PlannedVsActualChart({
  data,
  height = 240,
}: {
  data: PlannedVsActualPoint[]
  height?: number
}) {
  const { t, i18n } = useTranslation()

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        ...point,
        label: new Date(point.date).toLocaleDateString(i18n.language === "en" ? "en-US" : i18n.language, {
          month: "short",
          day: "numeric",
        }),
      })),
    [data, i18n.language]
  )

  if (chartData.length === 0) {
    return (
      <div
        className="flex h-40 items-center justify-center rounded-md border border-dashed border-input text-center text-sm text-muted-foreground"
        role="status"
      >
        {t("analytics.noPlannedWater")}
      </div>
    )
  }

  return (
    <div style={{ height }} role="img" aria-label={t("analytics.plannedVsActualLabel")}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
          <XAxis dataKey="label" tick={AXIS_STYLE} minTickGap={16} />
          <YAxis tick={AXIS_STYLE} tickFormatter={(value) => formatLitres(value, i18n.language)} width={68} />
          <Tooltip
            formatter={(value: any, name: any) => [
              formatLitres(value == null ? null : Number(value), i18n.language),
              name === "planned_litres" ? t("analytics.planned") : t("analytics.actual"),
            ]}
            contentStyle={TOOLTIP_STYLE}
          />
          <Legend
            formatter={(value) => (value === "planned_litres" ? t("analytics.planned") : t("analytics.actual"))}
            iconType="circle"
            iconSize={8}
            wrapperStyle={{ fontSize: 12, display: "flex", gap: "1rem" }}
          />
          <Bar dataKey="planned_litres" fill="rgb(var(--muted-foreground))" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          <Bar dataKey="actual_litres" fill="rgb(var(--primary))" radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/** Weekly / monthly consumption trend as a line. */
export function WaterTrendChart({
  data,
  granularity = "week",
  height = 220,
}: {
  data: WaterSeriesPoint[]
  granularity?: "week" | "month"
  height?: number
}) {
  const { t, i18n } = useTranslation()

  const chartData = useMemo(
    () =>
      data.map((point) => ({
        ...point,
        label:
          granularity === "month"
            ? point.bucket
            : new Date(point.bucket).toLocaleDateString(i18n.language === "en" ? "en-US" : i18n.language, {
                month: "short",
                day: "numeric",
              }),
      })),
    [data, granularity, i18n.language]
  )

  if (chartData.length === 0) {
    return (
      <div
        className="flex h-40 items-center justify-center rounded-md border border-dashed border-input text-center text-sm text-muted-foreground"
        role="status"
      >
        {t("analytics.noMeasuredWater")}
      </div>
    )
  }

  return (
    <div style={{ height }} role="img" aria-label={t("analytics.trendChartLabel")}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 12, bottom: 0, left: -8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
          <XAxis dataKey="label" tick={AXIS_STYLE} minTickGap={16} />
          <YAxis tick={AXIS_STYLE} tickFormatter={(value) => formatLitres(value, i18n.language)} width={68} />
          <Tooltip
            formatter={(value: any) => [formatLitres(value == null ? null : Number(value), i18n.language), t("analytics.waterUsed")]}
            contentStyle={TOOLTIP_STYLE}
          />
          <Line
            type="monotone"
            dataKey="litres"
            stroke="rgb(var(--secondary))"
            strokeWidth={2}
            dot={{ r: 3 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Soil moisture over time with the crop target band.
 *
 * Missing observations are rendered as gaps: the line is never bridged
 * across a missing reading.
 */
export function MoistureTrendChart({
  data,
  bandLow,
  bandHigh,
  height = 260,
  label,
}: {
  data: Array<{ time: string; moisture: number | null }>
  bandLow?: number | null
  bandHigh?: number | null
  height?: number
  label?: string
}) {
  const { t } = useTranslation()

  if (data.length === 0) {
    return (
      <div
        className="flex h-40 items-center justify-center rounded-md border border-dashed border-input text-center text-sm text-muted-foreground"
        role="status"
      >
        {t("analytics.noMoistureReadings")}
      </div>
    )
  }

  return (
    <div style={{ height }} role="img" aria-label={label || t("analytics.moistureTrendLabel")}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} className="text-muted-foreground/20" />
          <XAxis dataKey="time" tick={AXIS_STYLE} minTickGap={24} />
          <YAxis domain={[0, 100]} tick={AXIS_STYLE} width={44} />
          <Tooltip
            formatter={(value: any) => [value == null ? "—" : `${Number(value).toFixed(1)}%`, t("common.moisture")]}
            contentStyle={TOOLTIP_STYLE}
          />
          {bandLow != null && bandHigh != null && (
            <ReferenceArea
              y1={bandLow}
              y2={bandHigh}
              fill="rgb(var(--healthy))"
              fillOpacity={0.08}
              stroke="none"
              label={{ value: t("guidance.targetBand"), position: "insideTopLeft", fontSize: 10, fill: "rgb(var(--muted-foreground))" }}
            />
          )}
          <Line
            type="monotone"
            dataKey="moisture"
            stroke="rgb(var(--primary))"
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
