"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Switch({
  className,
  checked,
  onCheckedChange,
  ...props
}: {
  className?: string
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
} & React.HTMLAttributes<HTMLSpanElement>) {
  const state = checked ? "checked" : "unchecked"
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onCheckedChange?.(!checked)}
      className={cn(
        "inline-flex items-center justify-center cursor-pointer rounded-full border border-input bg-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        state === "checked" ? "bg-primary" : "bg-input",
        className
      )}
      {...props}
    >
      <span
        className={cn(
          "pointer-events-none block rounded-full bg-background shadow ring-0 h-4 w-4 transition-transform",
          state === "checked" ? "translate-x-4 border-primary" : "",
        )}
      />
    </button>
  )
}
