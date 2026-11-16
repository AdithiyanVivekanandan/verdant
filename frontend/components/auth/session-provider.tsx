"use client"

import { useEffect, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import type { AuthChangeEvent, Session } from "@supabase/supabase-js"
import { api, setSupabaseClient } from "@/lib/api"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

export function SessionProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [supabase] = useState(() => createBrowserSupabaseClient())
  const ensuredUser = useRef<string | null>(null)
  const ensureInFlight = useRef<Promise<void> | null>(null)

  useEffect(() => {
    setSupabaseClient(supabase)
  }, [supabase])

  useEffect(() => {
    let mounted = true
    let subscription: { unsubscribe: () => void } | undefined

    const ensureProfile = async (userId: string) => {
      if (!mounted || ensuredUser.current === userId) return
      if (!ensureInFlight.current) {
        ensureInFlight.current = api
          .post("/api/v1/auth/profile")
          .then(() => {
            ensuredUser.current = userId
          })
          .catch(() => {
            // Profile may already exist; subsequent requests carry the bearer token.
          })
          .finally(() => {
            ensureInFlight.current = null
          })
      }
      await ensureInFlight.current
    }

    const initialize = async () => {
      const { data } = await supabase.auth.getSession()
      if (mounted && data.session?.user) {
        await ensureProfile(data.session.user.id)
      }
    }

    initialize()

    try {
      const { data } = supabase.auth.onAuthStateChange(
        async (event: AuthChangeEvent, session: Session | null) => {
          if (!mounted) return
          if (event === "SIGNED_IN" && session?.user) {
            await ensureProfile(session.user.id)
          }
          if (event === "SIGNED_OUT") {
            ensuredUser.current = null
            ensureInFlight.current = null
            router.push("/auth/login")
          }
        },
      )
      subscription = data?.subscription
    } catch {
      // Older providers or a missing configuration can return no subscription.
      subscription = undefined
    }

    return () => {
      mounted = false
      subscription?.unsubscribe?.()
    }
  }, [supabase, router])

  return <>{children}</>
}
