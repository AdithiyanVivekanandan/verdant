"use client"

import { useEffect, useState } from "react"
import i18n, { type Language } from "@/lib/i18n"

export function useLanguage() {
  const [language, setLanguageState] = useState<Language>(
    (i18n.language as Language) || "en",
  )

  useEffect(() => {
    const stored = localStorage.getItem("language") as Language | null
    const lang = stored || "en"
    setLanguageState(lang)
    i18n.changeLanguage(lang)
  }, [])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem("language", lang)
    i18n.changeLanguage(lang)
  }

  return { language, setLanguage }
}
