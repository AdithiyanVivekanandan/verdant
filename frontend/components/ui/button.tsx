"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

function Slot({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLElement> & { children: React.ReactNode }) {
  if (!React.isValidElement(children)) {
    return (
      <span className={className} {...props}>
        {children}
      </span>
    )
  }
  return React.cloneElement(
    children as React.ReactElement<{ className?: string }>,
    {
      ...props,
      className: cn(className, (children.props as { className?: string }).className),
    }
  )
}

export function Button({
  className,
  variant,
  size,
  disabled = false,
  loading = false,
  asChild = false,
  children,
  ...props
}: {
  className?: string
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link"
    | "caution"
    | "healthy"
    | "info"
  size?: "default" | "sm" | "lg" | "icon"
  disabled?: boolean
  loading?: boolean
  asChild?: boolean
  children: React.ReactNode
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const Comp: React.ElementType = asChild ? Slot : "button"
  const buttonProps: Record<string, unknown> = asChild
    ? {}
    : { disabled: disabled || loading, type: "button" as const }

  const variantResolved = variant || "default"
  const sizeResolved = size || "default"

  const variants = {
    default: "bg-primary text-primary-foreground hover:bg-primary/90",
    destructive:
      "bg-destructive text-destructive-foreground hover:bg-destructive/90",
    outline:
      "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
    secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/90",
    ghost: "hover:bg-accent hover:text-accent-foreground",
    link: "text-primary underline-offset-4 hover:underline",
    caution: "bg-caution text-caution-foreground hover:bg-caution/90",
    healthy: "bg-healthy text-healthy-foreground hover:bg-healthy/90",
    info: "bg-info text-info-foreground hover:bg-info/90",
  }

  const sizes = {
    default: "h-11 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-12 rounded-md px-8",
    icon: "h-11 w-11",
  }

  return (
    <Comp
      {...buttonProps}
      className={cn(
        "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        loading && "opacity-70 pointer-events-none",
        variants[variantResolved],
        sizes[sizeResolved],
        className
      )}
      {...props}
    >
      {children}
    </Comp>
  )
}
