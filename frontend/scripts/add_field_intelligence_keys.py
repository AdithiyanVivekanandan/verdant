#!/usr/bin/env python3
"""Insert the `fieldDetail.intelligence` translation section.

The section is nested inside the existing `fieldDetail` object of every
locale file. The script is idempotent: it skips a locale that already has
the section.
"""
from __future__ import annotations

import re
from pathlib import Path

TRANSLATIONS = Path(__file__).resolve().parents[1] / "lib" / "translations"

SECTION: dict[str, dict[str, str]] = {
    "en": {
        "title": "Field intelligence",
        "requirementTitle": "Irrigation requirement",
        "noPrediction": "No requirement can be estimated yet",
        "noPredictionDescription": "Record a soil moisture reading for this field so Verdant can estimate the water requirement.",
        "currentMoisture": "Current moisture",
        "predictedMoisture": "Moisture in 24 hours",
        "requirementMm": "Water requirement",
        "estimatedVolume": "Estimated volume",
        "modelSource": "Prediction source",
        "confidence": "Confidence",
        "dataFreshness": "Data freshness",
        "calculationVersion": "Calculation version",
        "howCalculated": "How this was calculated",
        "rootDepth": "Rooting depth",
        "cropCoefficient": "Crop coefficient (Kc)",
        "et0": "Reference evapotranspiration",
        "cropWaterUse": "Crop water use",
        "depletion": "Soil water deficit",
        "effectiveRainfall": "Effective rainfall",
        "area": "Field area",
        "efficiency": "Application efficiency",
        "notSet": "Not set",
        "missingInputs": "Missing inputs",
        "scheduleTitle": "Schedule for this field",
        "waterTitle": "Water used by this field",
        "waterApplied": "Water applied",
        "predictionHistoryTitle": "Prediction history",
        "settingsTitle": "Application settings",
        "settingsDescription": "These optional values let Verdant convert a water depth into litres and minutes. Verdant does not estimate them when they are not set.",
        "applicationMethod": "Application method",
        "applicationRate": "Application rate",
        "waterSource": "Water source",
    },
    "hi": {
        "title": "खेत की जानकारी",
        "requirementTitle": "सिंचाई आवश्यकता",
        "noPrediction": "अभी आवश्यकता का अनुमान नहीं लगाया जा सकता",
        "noPredictionDescription": "इस खेत के लिए मृदा नमी रीडिंग दर्ज करें ताकि वर्डन्ट जल आवश्यकता का अनुमान लगा सके।",
        "currentMoisture": "वर्तमान नमी",
        "predictedMoisture": "24 घंटे बाद की नमी",
        "requirementMm": "जल आवश्यकता",
        "estimatedVolume": "अनुमानित मात्रा",
        "modelSource": "पूर्वानुमान स्रोत",
        "confidence": "विश्वास",
        "dataFreshness": "डेटा की ताजगी",
        "calculationVersion": "गणना संस्करण",
        "howCalculated": "यह कैसे निकाला गया",
        "rootDepth": "जड़ की गहराई",
        "cropCoefficient": "फसल गुणांक (Kc)",
        "et0": "संदर्भ वाष्पीकरण",
        "cropWaterUse": "फसल जल उपयोग",
        "depletion": "मृदा जल की कमी",
        "effectiveRainfall": "प्रभावी वर्षा",
        "area": "खेत का क्षेत्र",
        "efficiency": "आवेदन दक्षता",
        "notSet": "सेट नहीं है",
        "missingInputs": "अनुपलब्ध इनपुट",
        "scheduleTitle": "इस खेत की अनुसूची",
        "waterTitle": "इस खेत में उपयोग किया गया जल",
        "waterApplied": "डाला गया जल",
        "predictionHistoryTitle": "पूर्वानुमान इतिहास",
        "settingsTitle": "आवेदन सेटिंग्स",
        "settingsDescription": "ये वैकल्पिक मान वर्डन्ट को गहराई को लीटर और मिनट में बदलने देते हैं। सेट न होने पर वर्डन्ट इन्हें अनुमानित नहीं करता।",
        "applicationMethod": "आवेदन विधि",
        "applicationRate": "आवेदन दर",
        "waterSource": "जल स्रोत",
    },
    "kn": {
        "title": "ಹೊಲದ ಮಾಹಿತಿ",
        "requirementTitle": "ನೀರಾವರಿ ಅಗತ್ಯ",
        "noPrediction": "ಇನ್ನೂ ಅಗತ್ಯವನ್ನು ಅಂದಾಜಿಸಲಾಗುತ್ತಿಲ್ಲ",
        "noPredictionDescription": "ಈ ಹೊಲಕ್ಕೆ ಮಣ್ಣಿನ ತೇವಾಂಶ ಓದುವಿಕೆ ದಾಖಲಾಸಿ, ನೀರಿನ ಅಗತ್ಯ ಅಂದಾಜಿಸಲು ವರ್ಡನ್ಟ್‌ಗೆ ಸಹಾಯ ಮಾಡಿ.",
        "currentMoisture": "ಪ್ರಸ್ತುತ ತೇವಾಂಶ",
        "predictedMoisture": "24 ಗಂಟೆಗಳ ನಂತರದ ತೇವಾಂಶ",
        "requirementMm": "ನೀರಿನ ಅಗತ್ಯ",
        "estimatedVolume": "ಅಂದಾಜು ಪ್ರಮಾಣ",
        "modelSource": "ಮುನ್ಸೂಚನೆಯ ಮೂಲ",
        "confidence": "ವಿಶ್ವಾಸ",
        "dataFreshness": "ಡೇಟಾದ ತಾಜಾಪು",
        "calculationVersion": "ಲೆಕ್ಕಾಚಾರ ಆವೃತ್ತಿ",
        "howCalculated": "ಇದು ಹೇಗೆ ಲೆಕ್ಕಾಚಾರ ಮಾಡಲಾಗಿದೆ",
        "rootDepth": "ಬುಡದ ಆಳವು",
        "cropCoefficient": "ಬೆಳೆ ಗುಣಕ (Kc)",
        "et0": "ಉಲ್ಲೇಖ ಆವಿಷ್ಟನ",
        "cropWaterUse": "ಬೆಳೆ ನೀರಿನ ಬಳಕೆ",
        "depletion": "ಮಣ್ಣಿನ ನೀರಿನ ಕೊರತೆ",
        "effectiveRainfall": "ಪರಿಣಾಮಕಾರಿ ಮಳೆ",
        "area": "ಹೊಲದ ವಿಸ್ತೀರ್ಣ",
        "efficiency": "ಅನ್ವಯದ ದಕ್ಷತೆ",
        "notSet": "ಹೊಂದಿಸಿಲ್ಲ",
        "missingInputs": "ಇಲ್ಲದ ಇನ್ಪುಟ್‌ಗಳು",
        "scheduleTitle": "ಈ ಹೊಲದ ನಿಗದಿ",
        "waterTitle": "ಈ ಹೊಲದಲ್ಲಿ ಬಳಸಿದ ನೀರು",
        "waterApplied": "ಹಾಕಿದ ನೀರು",
        "predictionHistoryTitle": "ಮುನ್ಸೂಚನೆಯ ಇತಿಹಾಸ",
        "settingsTitle": "ಅನ್ವಯ ಸೆಟ್ಟಿಂಗ್‌ಗಳು",
        "settingsDescription": "ಈ ಐಚ್ಛಿಕ ಮೌಲ್ಯಗಳು ವರ್ಡನ್ಟ್‌ಗೆ ಆಳವನ್ನು ಲೀಟರ್ ಮತ್ತು ನಿಮಿಷಗಳಾಗಿ ಪರಿವರ್ತಿಸಲು ಸಹಾಯ ಮಾಡುತ್ತವೆ. ಹೊಂದಿಸದಾಗ ವರ್ಡನ್ಟ್ ಅವುಗಳನ್ನು ಅಂದಾಜಿಸುವುದಿಲ್ಲ.",
        "applicationMethod": "ಅನ್ವಯ ವಿಧಾನ",
        "applicationRate": "ಅನ್ವಯ ದರ",
        "waterSource": "ನೀರಿನ ಮೂಲ",
    },
    "ta": {
        "title": "தோட்ட அறிவு",
        "requirementTitle": "பாசன தேவை",
        "noPrediction": "தேவையை இன்னும் மதிப்பிட முடியவில்லை",
        "noPredictionDescription": "இந்தத் தோட்டத்திற்கு மண் ஈரப்பத பதிவைப் பதிவிசெய்து, நீர்த் தேவையை மதிப்பிட வெர்டென்டுக்கு உதவுங்கள்.",
        "currentMoisture": "தற்போதைய ஈரப்பதம்",
        "predictedMoisture": "24 மணி நேரத்திலுள்ள ஈரப்பதம்",
        "requirementMm": "நீர்த் தேவை",
        "estimatedVolume": "மதிப்பிடப்பட்ட அளவு",
        "modelSource": "முன்னறிஞ்சல் மூலம்",
        "confidence": "நம்பிக்கை",
        "dataFreshness": "தரவு புதுத்தன்மை",
        "calculationVersion": "கணக்கீடு பதிப்பு",
        "howCalculated": "இது எப்படி கணக்கிடப்பட்டது",
        "rootDepth": "வேர் ஆழம்",
        "cropCoefficient": "பயிர் குறைவீடு (Kc)",
        "et0": "ஆதார் நீராவிப்போக்கு",
        "cropWaterUse": "பயிர் நீர் பயன்பாடு",
        "depletion": "மண் நீர் குறைவு",
        "effectiveRainfall": "விளைவுக்குரிய மழை",
        "area": "தோட்டப் பரப்பு",
        "efficiency": "பயன்பாட்டு திறன்",
        "notSet": "அமைக்கப்படவில்லை",
        "missingInputs": "இல்லாத உள்ளீடுகள்",
        "scheduleTitle": "இந்தத் தோட்டத்தின் அட்டவணை",
        "waterTitle": "இந்தத் தோட்டத்தில் பயன்படுத்திய நீர்",
        "waterApplied": "வழங்கிய நீர்",
        "predictionHistoryTitle": "முன்னறிஞ்சல் வரலாறு",
        "settingsTitle": "பயன்பாட்டு அமைப்புகள்",
        "settingsDescription": "இந்த விருப்பத் தரவுகள் ஆழத்தை லிட்டர் மற்றும் நிமிடங்களாக மாற்ற உதவும். அமைக்கப்படாதபோது வெர்டென்ட் அவற்றை மதிப்பிடாது.",
        "applicationMethod": "பயன்பாட்டு முறை",
        "applicationRate": "பயன்பாட்டு வீதம்",
        "waterSource": "நீர் மூலம்",
    },
}


def find_field_detail(text: str) -> int:
    for marker in ("\n  fieldDetail: {", '\n  "fieldDetail": {'):
        if marker in text:
            return text.index(marker)
    raise ValueError("fieldDetail section not found")


def main() -> None:
    for locale, section in SECTION.items():
        path = TRANSLATIONS / f"{locale}.ts"
        text = path.read_text(encoding="utf-8")
        if re.search(r"\n\s*intelligence: \{", text) or re.search(r'\n\s*"intelligence": \{', text):
            print(f"{locale}: already present")
            continue
        index = find_field_detail(text)
        brace = text.index("{", index) + 1
        spread = re.search(r"\n\s*\.\.\.en\.fieldDetail,", text[brace:])
        if spread:
            brace += spread.end()
        block = ["\n    intelligence: {"]
        for key, value in section.items():
            block.append(f'      {key}: "{value}",')
        block.append("    },")
        text = text[:brace] + "\n".join(block) + text[brace:]
        path.write_text(text, encoding="utf-8")
        print(f"{locale}: inserted")


if __name__ == "__main__":
    main()
