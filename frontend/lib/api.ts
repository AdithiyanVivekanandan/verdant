import type { Language } from "@/lib/i18n"
import { createBrowserSupabaseClient } from "@/lib/supabase/client"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

let supabase: any = null
let language: Language = "en"

export function setSupabaseClient(client: any) {
  supabase = client
}
export function setLanguage(lang: Language) {
  language = lang
}

async function getSupabaseClient() {
  if (!supabase && typeof window !== "undefined") {
    supabase = createBrowserSupabaseClient()
  }
  return supabase
}

export async function getToken(): Promise<string | null> {
  try {
    const client = await getSupabaseClient()
    if (!client) return null
    const { data } = await client.auth.getSession()
    const session = data?.session
    if (!session) {
      // If no session cached, try a refresh if refresh token exists in cookies
      const { data: refreshData } = await client.auth.refreshSession().catch(() => ({ data: { session: null } }))
      return refreshData?.session?.access_token ?? null
    }

    // If access token is about to expire within 30 seconds, refresh proactively
    if (session.expires_at && session.expires_at * 1000 < Date.now() + 30000) {
      const { data: refreshed } = await client.auth.refreshSession().catch(() => ({ data: { session: null } }))
      return refreshed?.session?.access_token ?? session.access_token
    }

    return session.access_token ?? null
  } catch {
    return null
  }
}

async function request(path: string, opts: RequestInit = {}): Promise<Response> {
  let token = await getToken()

  const buildHeaders = (t: string | null) => {
    const h: Record<string, string> = {
      "Content-Type": "application/json",
      "Accept-Language": language,
      ...(opts.headers as Record<string, string> || {}),
    }
    if (t) {
      h["Authorization"] = `Bearer ${t}`
    }
    return h
  }

  let res = await fetch(`${API_BASE}${path}`, {
    ...opts,
    headers: buildHeaders(token),
  })

  // If unauthorized and running in browser, attempt one token refresh and retry
  if (res.status === 401 && typeof window !== "undefined") {
    try {
      const client = await getSupabaseClient()
      if (client) {
        const { data: refreshData } = await client.auth.refreshSession().catch(() => ({ data: { session: null } }))
        const newToken = refreshData?.session?.access_token
        if (newToken) {
          res = await fetch(`${API_BASE}${path}`, {
            ...opts,
            headers: buildHeaders(newToken),
          })
        }
      }
    } catch {
      // Proceed with original 401 response
    }
  }

  return res
}

export async function apiJson<T = any>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await request(path, opts)
  let body: any = null
  const ct = res.headers.get("content-type") || ""
  if (ct.includes("application/json")) {
    body = await res.json()
  } else {
    body = await res.text()
  }
  if (!res.ok) {
    let msg = body && body.detail ? body.detail : body
    // Prevent displaying technical authorization errors directly to users
    if (res.status === 401) {
      msg = "Your session has expired. Please sign in again."
    }
    const err: any = new Error(typeof msg === "string" ? msg : JSON.stringify(msg))
    err.status = res.status
    err.body = body
    throw err
  }
  return body as T
}

export const api = {
  get: <T = any>(path: string, opts?: RequestInit) => apiJson<T>(path, { ...opts, method: "GET" }),
  post: <T = any>(path: string, body?: any, opts?: RequestInit) =>
    apiJson<T>(path, { ...opts, method: "POST", body: body ? JSON.stringify(body) : undefined }),
  put: <T = any>(path: string, body?: any, opts?: RequestInit) =>
    apiJson<T>(path, { ...opts, method: "PUT", body: body ? JSON.stringify(body) : undefined }),
  patch: <T = any>(path: string, body?: any, opts?: RequestInit) =>
    apiJson<T>(path, { ...opts, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
  del: <T = any>(path: string, opts?: RequestInit) => apiJson<T>(path, { ...opts, method: "DELETE" }),
}
