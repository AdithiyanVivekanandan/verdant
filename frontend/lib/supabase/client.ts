import { createBrowserClient, isBrowser } from "@supabase/ssr"

let _client: any = null

export function createBrowserSupabaseClient() {
  if (_client) return _client
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  if (!url || !key) {
    // Return a no-op client during build/missing config
    _client = {
      auth: {
        signInWithPassword: async () => ({ data: null, error: { message: "Supabase not configured" } }),
        signInWithOAuth: async () => ({ error: { message: "Supabase not configured" } }),
        signUp: async () => ({ data: null, error: { message: "Supabase not configured" } }),
        getUser: async () => ({ data: { user: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
        signOut: async () => ({ error: null }),
      },
    }
    return _client
  }
  _client = createBrowserClient(url, key)
  return _client
}

export const isClient = isBrowser()
