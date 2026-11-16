"use client"

import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { AppSidebar } from "@/components/layout/sidebar"
import { TopBar } from "@/components/layout/top-bar"

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [router])

  if (!mounted) return null

  return (
    <div className="relative">
      <AppSidebar />
      <div className="md:pl-64 min-h-screen">
        <TopBar />
        <main className="pt-6 pb-10 px-6">{children}</main>
      </div>
    </div>
  )
}
