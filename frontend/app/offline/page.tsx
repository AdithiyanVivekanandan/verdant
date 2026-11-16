export default function OfflinePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-2xl font-semibold">You are offline</h1>
      <p className="max-w-md text-muted-foreground">
        Verdant could not reach the network. Cached pages remain available, and
        your data will sync automatically once the connection returns.
      </p>
      <a href="/dashboard" className="text-sm underline">
        Try again
      </a>
    </main>
  )
}
