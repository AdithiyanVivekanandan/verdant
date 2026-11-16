"use client"

import { useState } from "react"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectOption } from "@/components/ui/select"
import { Clock, Calendar } from "lucide-react"

const OPTIONS = [
  { value: "24h", icon: Clock, labelKey: "dashboard.chart.hours24" },
  { value: "7d", icon: Calendar, labelKey: "dashboard.chart.days7" },
  { value: "30d", icon: Calendar, labelKey: "dashboard.chart.days30" },
]

export function Dropdown({ value, onChange, t }: { value: "24h" | "7d" | "30d"; onChange: (v: "24h" | "7d" | "30d") => void; t: (key: string) => string }) {
  const opt = OPTIONS.find((o) => o.value === value)
  return (
    <Select value={value} onChange={(e) => onChange(e.target.value as any)} className="w-32">
      <SelectTrigger className="h-9 text-xs">
        <SelectValue>{t(opt?.labelKey || "dashboard.chart.days7")}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {OPTIONS.map((o) => (
          <SelectOption key={o.value} value={o.value}>
            {t(o.labelKey)}
          </SelectOption>
        ))}
      </SelectContent>
    </Select>
  )
}
