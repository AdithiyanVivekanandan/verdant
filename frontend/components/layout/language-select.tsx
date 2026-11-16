"use client"

import { Globe } from "lucide-react"
import { useTranslation } from "react-i18next"
import { useLanguage } from "@/components/layout/i18n-provider"
import { LANGUAGE_NAMES } from "@/lib/i18n"
import type { Language } from "@/lib/i18n"

const LANGUAGES: Language[] = ["en", "hi", "kn", "ta"]

export function LanguageSelect({
  compact = false,
  className = "",
}: {
  compact?: boolean
  className?: string
}) {
  const { t } = useTranslation()
  const { language, setLanguage } = useLanguage()

  return (
    <label
      className={`inline-flex items-center gap-2 rounded-md border border-input bg-background px-2.5 py-1.5 text-sm ${className}`}
    >
      <Globe className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      <span className={compact ? "sr-only" : "sr-only sm:not-sr-only"}>
        {t("common.language")}
      </span>
      <select
        value={language}
        onChange={(event) => setLanguage(event.target.value as Language)}
        aria-label={t("common.language")}
        className="max-w-[8.5rem] cursor-pointer bg-transparent text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {LANGUAGES.map((code) => (
          <option key={code} value={code}>
            {LANGUAGE_NAMES[code]}
          </option>
        ))}
      </select>
    </label>
  )
}
