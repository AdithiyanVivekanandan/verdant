"use client"

import React from "react"
import { cn } from "@/lib/utils"

export function PageContainer({
  className,
  children,
}: {
  className?: string
  children: React.ReactNode
}) {
  return (
    <main
      id="main"
      className={cn(
        "mx-auto w-full max-w-[1360px] flex-1 px-4 py-6 pb-24 sm:px-6 lg:px-8 lg:pb-10",
        className
      )}
    >
      {children}
    </main>
  )
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {description && <p className="text-muted-foreground text-sm mt-1">{description}</p>}
      </div>
      {action && (
        <div className="flex items-center gap-2">{action}</div>
      )}
    </div>
  )
}
