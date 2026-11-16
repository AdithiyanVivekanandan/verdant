"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Badge({
  className,
  variant,
  children,
  ...props
}: {
  className?: string
  variant?: "default" | "secondary" | "destructive" | "caution" | "healthy" | "info"
  children: React.ReactNode
} & React.HTMLAttributes<HTMLSpanElement>) {
  const variantResolved = variant || "default"
  const variants = {
    default: "bg-muted text-muted-foreground",
    secondary: "bg-secondary text-secondary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    caution: "bg-caution text-caution-foreground",
    healthy: "bg-healthy text-healthy-foreground",
    info: "bg-info text-info-foreground",
  }
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        variants[variantResolved],
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
