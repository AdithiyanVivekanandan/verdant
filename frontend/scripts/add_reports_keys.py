#!/usr/bin/env python3
"""Insert the reports and guidance-page translation keys.

The script is idempotent: a key that already exists is skipped.
"""
from __future__ import annotations

from pathlib import Path

TRANSLATIONS = Path(__file__).resolve().parents[1] / "lib" / "translations"

ANALYTICS: dict[str, dict[str, str]] = {
    "en": {
        "reportsTitle": "Water usage reports",
        "reportsSubtitle": "Measured irrigation water, compared across fields, crops and periods.",
        "coreMetrics": "Core metrics",
        "today": "Today",
        "thisWeek": "This week",
        "thisMonth": "This month",
        "day": "Daily",
        "week": "Weekly",
        "month": "Monthly",
        "granularity": "Time granularity",
        "consumption": "Water consumption",
        "comparisons": "Comparisons",
        "periodComparison": "Current period against the previous period",
        "change": "Change",
        "noPreviousData": "No data for the previous period",
        "measuredEventsTitle": "Measured irrigation by day",
        "estimateVsActualTitle": "Estimated against actual, per schedule",
        "difference": "Difference",
        "date": "Date",
        "eventsCount": "{{count}} events",
        "perWeek": "{{count}} times a week",
        "daysValue": "{{count}} days",
        "averageInterval": "Average interval between irrigations",
        "unitNote": "Volumes are shown in litres (L), kilolitres (kL) and megalitres (ML). A litre per acre figure is the measured volume divided by the field area.",
        "unmeasuredNote": "These events are excluded from every total because no volume was measured.",
        "noMoistureReadingsNote": "No soil moisture readings.",
    },
    "hi": {
        "reportsTitle": "जल उपयोग रिपोर्ट",
        "reportsSubtitle": "मापा गया सिंचाई जल, खेतों, फसलों और अवधियों के अनुसार तुलना के साथ।",
        "coreMetrics": "मुख्य माप",
        "today": "आज",
        "thisWeek": "इस सप्ताह",
        "thisMonth": "इस माह",
        "day": "दैनिक",
        "week": "साप्ताहिक",
        "month": "मासिक",
        "granularity": "समय स्तर",
        "consumption": "जल उपभोग",
        "comparisons": "तुलनाएं",
        "periodComparison": "वर्तमान अवधि बनाम पिछली अवधि",
        "change": "परिवर्तन",
        "noPreviousData": "पिछली अवधि का कोई डेटा नहीं",
        "measuredEventsTitle": "दिन के अनुसार मापी गई सिंचाई",
        "estimateVsActualTitle": "अनुसूचीवार अनुमान बनाम वास्तविक",
        "difference": "अंतर",
        "date": "तारीख",
        "eventsCount": "{{count}} घटनाएं",
        "perWeek": "सप्ताह में {{count}} बार",
        "daysValue": "{{count}} दिन",
        "averageInterval": "सिंचाई के बीच औसत अंतराल",
        "unitNote": "मात्रा लीटर (L), किलोलीटर (kL) और मेगालीटर (ML) में दिखाई जाती है। प्रति एकड़ लीटर मापा गया आयतन को खेत के क्षेत्र से भाग देकर निकाला जाता है।",
        "unmeasuredNote": "इन घटनाओं को हर कुल से बाहर रखा गया है क्योंकि मात्रा मापी नहीं गई।",
        "noMoistureReadingsNote": "कोई मृदा नमी रीडिंग नहीं।",
    },
    "kn": {
        "reportsTitle": "ನೀರಿನ ಬಳಕೆಯ ವರದಿ",
        "reportsSubtitle": "ಅಳೆದ ನೀರಾವರಿ ನೀರು, ಹೊಲಗಳು, ಬೆಳೆಗಳು ಮತ್ತು ಅವಧಿಗಳ ನಡುವೆ ಹೋಲಿಕೆಯೊಂದಿಗೆ.",
        "coreMetrics": "ಮುಖ್ಯ ಅಳತೆ",
        "today": "ಇಂದು",
        "thisWeek": "ಈ ವಾರ",
        "thisMonth": "ಈ ತಿಂಗಳು",
        "day": "ದೈನಂದಿನ",
        "week": "ವಾರದ",
        "month": "ಮಾಸಿಕ",
        "granularity": "ಸಮಯ ಮಟ್ಟ",
        "consumption": "ನೀರಿನ ಬಳಕೆ",
        "comparisons": "ಹೋಲಿಕೆಗಳು",
        "periodComparison": "ಪ್ರಸ್ತುತ ಅವಧಿ ಮತ್ತು ಹಿಂದಿನ ಅವಧಿ",
        "change": "ಬದಲಾವಣೆ",
        "noPreviousData": "ಹಿಂದಿನ ಅವಧಿಯ ಡೇಟಾ ಇಲ್ಲ",
        "measuredEventsTitle": "ದಿನದ ಪ್ರಕಾರ ಅಳೆದ ನೀರಾವರಿ",
        "estimateVsActualTitle": "ನಿಗದಿಯಂತೆ ಅಂದಾಜು ಮತ್ತು ನಿಜವಾದ",
        "difference": "ವ್ಯತ್ಯಾಸ",
        "date": "ದಿನಾಂಕ",
        "eventsCount": "{{count}} ಘಟನೆಗಳು",
        "perWeek": "ವಾರಕ್ಕೆ {{count}} ಬಾರಿ",
        "daysValue": "{{count}} ದಿನ",
        "averageInterval": "ನೀರಾವರಿಗಳ ನಡುವಿನ ಸರಾಸರಿ ಅಂತರ",
        "unitNote": "ಪ್ರಮಾಣವನ್ನು ಲೀಟರ್ (L), ಕಿಲೋಲೀಟರ್ (kL) ಮತ್ತು ಮೆಗಾಲೀಟರ್ (ML) ನಲ್ಲಿ ತೋರಿಸಲಾಗುತ್ತದೆ. ಎಕರೆಗೆ ಲೀಟರ್ ಅಳೆದ ಪ್ರಮಾಣವನ್ನು ಹೊಲದ ವಿಸ್ತೀರ್ಣದಿಂದ ಭಾಗಿಸಿ ಪಡೆಯಲಾಗುತ್ತದೆ.",
        "unmeasuredNote": "ಪ್ರಮಾಣ ಅಳೆಯದ ಕಾರಣ ಈ ಘಟನೆಗಳನ್ನು ಎಲ್ಲಾ ಒಟ್ಟಿನಿಂದ ಹೊರತುಪಡಿಸಲಾಗಿದೆ.",
        "noMoistureReadingsNote": "ಮಣ್ಣಿನ ತೇವಾಂಶ ಓದುವಿಕೆಗಳಿಲ್ಲ.",
    },
    "ta": {
        "reportsTitle": "நீர் பயன்பாடு அறிக்கைகள்",
        "reportsSubtitle": "அளவிடப்பட்ட பாசன நீர், தோட்டங்கள், பயிர்கள் மற்றும் காலகட்டங்களுக்கு இடையிலான ஒப்பீட்டுடன்.",
        "coreMetrics": "முக்கிய அளவீடுகள்",
        "today": "இன்று",
        "thisWeek": "இந்த வாரம்",
        "thisMonth": "இந்த மாதம்",
        "day": "தினையான",
        "week": "வாராந்திர",
        "month": "மாதாந்திர",
        "granularity": "கால நிலை",
        "consumption": "நீர் பயன்பாடு",
        "comparisons": "ஒப்பீடுகள்",
        "periodComparison": "தற்போதைய காலகட்டம் மற்றும் முந்தைய காலகட்டம்",
        "change": "மாற்றம்",
        "noPreviousData": "முந்தைய காலகட்டத்திற்கு தரவு இல்லை",
        "measuredEventsTitle": "நாள் வாரியாக அளவிடப்பட்ட பாசனம்",
        "estimateVsActualTitle": "அட்டவணைவாரி மதிப்பிட்டது மற்றும் உண்மையானது",
        "difference": "வேறுபாடு",
        "date": "தேதி",
        "eventsCount": "{{count}} நிகழ்வுகள்",
        "perWeek": "வாரத்திற்கு {{count}} தடவை",
        "daysValue": "{{count}} நாட்கள்",
        "averageInterval": "பாசனங்களுக்கு இடையிலான சராசரி இடைவெளி",
        "unitNote": "அளவுகள் லிட்டர் (L), கிலோலிட்டர் (kL) மற்றும் மெகாலிட்டர் (ML) ஆகியவற்றில் காட்டப்படுகின்றன. ஏக்கரைக்கான லிட்டர் என்பது அளவிடப்பட்ட அளவைத் தோட்டப் பரப்பால் பிரித்து கிடைக்கும்.",
        "unmeasuredNote": "அளவு அளவிடப்படாததால் இந்நிகழ்வுகள் ஒவ்வொரு மொத்தத்திலிருந்தும் விலக்கப்படுகின்றன.",
        "noMoistureReadingsNote": "மண் ஈரப்பத பதிவுகள் இல்லை.",
    },
}

SCHEDULE_EXTRA: dict[str, dict[str, str]] = {
    "en": {
        "needsIrrigation": "Needs irrigation",
        "canWait": "Can wait",
        "uncertain": "Uncertain — needs a current reading",
        "totalEstimatedToday": "Total estimated volume today",
    },
    "hi": {
        "needsIrrigation": "सिंचाई की आवश्यकता",
        "canWait": "प्रतीक्षा कर सकते हैं",
        "uncertain": "अनिश्चित — वर्तमान रीडिंग आवश्यक",
        "totalEstimatedToday": "आज की कुल अनुमानित मात्रा",
    },
    "kn": {
        "needsIrrigation": "ನೀರಾವರಿ ಅಗತ್ಯ",
        "canWait": "ಕಾಯಿರಿಯಬಹುದು",
        "uncertain": "ಅನಿಶ್ಚಿತ — ಪ್ರಸ್ತುತ ಓದುವಿಕೆ ಅಗತ್ಯ",
        "totalEstimatedToday": "ಇಂದಿನ ಒಟ್ಟು ಅಂದಾಜು ಪ್ರಮಾಣ",
    },
    "ta": {
        "needsIrrigation": "பாசனம் தேவை",
        "canWait": "காத்திருக்கலாம்",
        "uncertain": "நிச்சயமற்றது — புதிய பதிவு தேவை",
        "totalEstimatedToday": "இன்றைய மொத்த மதிப்பிட்ட அளவு",
    },
}


def add_keys(text: str, section: str, keys: dict[str, str]) -> str:
    marker = f"\n  {section}: {{"
    if marker not in text:
        return text
    index = text.index(marker)
    brace = text.index("{", index) + 1
    additions = "".join(
        f"\n    {key}: \"{value}\"," for key, value in keys.items() if f"{key}:" not in text
    )
    if not additions:
        return text
    return text[:brace] + additions + text[brace:]


def main() -> None:
    for locale in ("en", "hi", "kn", "ta"):
        path = TRANSLATIONS / f"{locale}.ts"
        text = path.read_text(encoding="utf-8")
        text = add_keys(text, "analytics", ANALYTICS[locale])
        text = add_keys(text, "schedule", SCHEDULE_EXTRA[locale])
        path.write_text(text, encoding="utf-8")
        print(f"updated {path.name}")


if __name__ == "__main__":
    main()
