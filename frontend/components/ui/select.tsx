"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Select({
  className,
  children,
  ...props
}: {
  className?: string
  children?: React.ReactNode
} & React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        "flex h-11 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
}

export function SelectTrigger(props: React.HTMLAttributes<HTMLSpanElement>) {
  return <span {...props} />
}

export function SelectValue(props: React.HTMLAttributes<HTMLSpanElement>) {
  return <span {...props} />
}

export function SelectContent(props: React.HTMLAttributes<HTMLDivElement>) {
  return <div {...props} />
}

export function SelectOption(props: React.OptionHTMLAttributes<HTMLOptionElement>) {
  return <option {...props} />
}

Select.Trigger = SelectTrigger
Select.Value = SelectValue
Select.Content = SelectContent
Select.Option = SelectOption
