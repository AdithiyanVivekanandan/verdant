"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Progress({
  className,
  value,
  ...props
}: {
  className?: string
  value: number
} & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex h-2 w-full overflow-hidden rounded-full border border-input bg-muted",
        className
      )}
      {...props}
    >
      <div
        className="h-full bg-primary"
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </div>
  )
}
