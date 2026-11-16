"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

export function Separator({
  className,
  ...props
}: {
  className?: string
} & React.HTMLAttributes<HTMLHRElement>) {
  return (
    <hr
      className={cn("-mx-px h-[1px] bg-border", className)}
      {...props}
    />
  )
}
