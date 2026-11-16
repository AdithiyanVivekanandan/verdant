"use client"

import { createContext, useContext, useEffect, useState } from "react"
import i18n, { type Language } from "@/lib/i18n"

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

export function I18nProvider({
  children,
}: {
  children: React.ReactNode
}) {
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

  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error("useLanguage must be used within I18nProvider")
  return ctx
}
