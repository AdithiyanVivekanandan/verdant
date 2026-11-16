"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Toast({
  className,
  variant,
  children,
  ...props
}: {
  className?: string
  variant?: "default" | "destructive" | "healthy" | "info"
  children: React.ReactNode
} & React.HTMLAttributes<HTMLDivElement>) {
  const variantResolved = variant || "default"
  const variants = {
    default: "bg-background text-foreground border border-input",
    destructive: "bg-destructive text-destructive-foreground",
    healthy: "bg-healthy text-healthy-foreground",
    info: "bg-info text-info-foreground",
  }
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border p-4 shadow-lg",
        variants[variantResolved],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function ToastTitle({
  className,
  children,
  ...props
}: {
  className?: string
  children: React.ReactNode
} & React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn("font-semibold", className)}
      {...props}
    >
      {children}
    </h3>
  )
}

export function ToastDescription({
  className,
  children,
  ...props
}: {
  className?: string
  children: React.ReactNode
} & React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    >
      {children}
    </p>
  )
}
