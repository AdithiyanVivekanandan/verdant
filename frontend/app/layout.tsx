import type { Metadata, Viewport } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { I18nProvider } from "@/components/layout/i18n-provider"
import { SessionProvider } from "@/components/auth/session-provider"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
})

export const metadata: Metadata = {
  title: "Verdant",
  description: "Smart Irrigation System for Predictive Water Management",
  manifest: "/manifest.json",
  icons: [
    {
      rel: "icon",
      type: "image/png",
      sizes: "192x192",
      url: "/icons/icon-192.png",
    },
    {
      rel: "icon",
      type: "image/png",
      sizes: "512x512",
      url: "/icons/icon-512.png",
    },
    {
      rel: "apple-touch-icon",
      sizes: "180x180",
      url: "/icons/apple-touch-icon.png",
    },
    {
      rel: "icon",
      type: "image/png",
      sizes: "32x32",
      url: "/icons/favicon-32.png",
    },
  ],
  openGraph: {
    siteName: "Verdant",
    title: "Verdant - Smart Irrigation",
    description: "Smart Irrigation System for Predictive Water Management and Crop Optimization",
  },
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#183D32" },
    { media: "(prefers-color-scheme: dark)", color: "#151D19" },
  ],
  width: "device-width",
  initialScale: 1,
}

const themeInitScript = `
(function () {
  try {
    var stored = localStorage.getItem('theme');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (stored === 'dark' || (!stored && prefersDark)) {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
})();
`

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans text-foreground antialiased">
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <I18nProvider>
          <SessionProvider>{children}</SessionProvider>
        </I18nProvider>
        {process.env.NODE_ENV === "production" ? (
          <script
            id="sw-register"
            dangerouslySetInnerHTML={{
              __html: `
                if ('serviceWorker' in navigator) {
                  window.addEventListener('load', () => {
                    navigator.serviceWorker.register('/sw.js').catch((err) => {
                      console.log('ServiceWorker registration failed', err)
                    })
                  })
                }
              `,
            }}
          />
        ) : (
          <script
            id="sw-unregister"
            dangerouslySetInnerHTML={{
              __html: `
                if ('serviceWorker' in navigator) {
                  navigator.serviceWorker.getRegistrations().then((regs) => {
                    regs.forEach((reg) => reg.unregister())
                  })
                  if (typeof caches !== 'undefined') {
                    caches.keys().then((keys) => keys.forEach((k) => caches.delete(k)))
                  }
                }
              `,
            }}
          />
        )}
      </body>
    </html>
  )
}
