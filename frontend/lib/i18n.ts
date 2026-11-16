import i18n from "i18next"
import { initReactI18next } from "react-i18next"

import en from "@/lib/translations/en"
import hi from "@/lib/translations/hi"
import kn from "@/lib/translations/kn"
import ta from "@/lib/translations/ta"

const resources = {
  en: { translation: en },
  hi: { translation: hi },
  kn: { translation: kn },
  ta: { translation: ta },
}

const LANGUAGE_NAMES: Record<string, string> = {
  en: "English",
  hi: "हिन्दी",
  kn: "ಕನ್ನಡ",
  ta: "தமிழ்",
}

export { resources, LANGUAGE_NAMES }

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: {
    escapeValue: false,
  },
})

export type Language = "en" | "hi" | "kn" | "ta"
export default i18n
