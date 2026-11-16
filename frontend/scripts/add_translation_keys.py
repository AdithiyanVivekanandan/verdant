#!/usr/bin/env python3
"""Insert the irrigation-intelligence translation sections into the locale files.

Run from the frontend directory:

    python3 scripts/add_translation_keys.py
"""
from __future__ import annotations

import re
from pathlib import Path

TRANSLATIONS = Path(__file__).resolve().parents[1] / "lib" / "translations"

# Each locale provides its own text. Keys are identical across locales so a
# missing key can never surface as a raw key in the interface.
SECTIONS: dict[str, dict[str, dict]] = {
    "en": {
        "analytics": {
            "noMeasuredWater": "No measured irrigation volume recorded yet.",
            "dailyConsumptionChartLabel": "Daily irrigation water consumption",
            "fieldUsageChartLabel": "Water used per field",
            "cropUsageChartLabel": "Water used per crop",
            "plannedVsActualLabel": "Planned against actual irrigation volume",
            "trendChartLabel": "Water consumption trend",
            "noMoistureReadings": "No soil moisture readings in this period.",
            "moistureTrendLabel": "Soil moisture trend",
            "waterUsed": "Water used",
            "planned": "Planned",
            "actual": "Actual",
            "noPlannedWater": "No planned irrigation recorded.",
            "moistureTrends": "Soil moisture trends",
            "selectField": "Select a field",
            "rangeLabel": "Time range",
            "customRange": "Custom",
            "from": "From",
            "to": "To",
            "bandFor": "Target band",
            "readingsShown": "Readings shown",
            "moistureTrendFor": "Soil moisture trend for {{field}}",
            "showDataTable": "Show the readings as a table",
            "gapNotice": "Missing measurements appear as gaps. Verdant never fills in a reading that was not recorded.",
            "dailyConsumption": "Daily consumption",
            "weeklyTrend": "Weekly trend",
            "monthlyTrend": "Monthly trend",
            "fieldWiseUsage": "Water used per field",
            "plannedVsActual": "Planned against actual",
            "moistureStatusDistribution": "Field condition summary",
            "cropWiseUsage": "Water used per crop",
            "fieldsNeedingMeasurements": "Fields needing updated measurements",
            "allFieldsUpdated": "Every field has a current reading.",
            "noIrrigationEvents": "No irrigation events have been recorded yet.",
            "dashboardFootnote": "Charts use measured values only. Planned irrigation is never counted as water used.",
            "litresPerAcre": "litres per acre",
            "averagePerEvent": "Average per irrigation",
            "frequency": "Irrigation frequency",
            "previousPeriod": "Previous period",
            "currentPeriod": "Current period",
            "totalWaterUsed": "Total water used",
            "measuredEvents": "Measured events",
            "unmeasuredEvents": "Events without a measurement",
        },
        "schedule": {
            "title": "Irrigation schedule",
            "emptyTitle": "No irrigation is scheduled today.",
            "emptyDescription": "No field currently needs irrigation. Verdant will show a recommendation when one does.",
            "decisionSupportNotice": "This schedule is decision support. Verdant does not control irrigation equipment; you decide whether and when to irrigate.",
            "priority": {
                "low": "Low",
                "medium": "Medium",
                "high": "High",
                "critical": "Critical",
                "uncertain": "Uncertain",
            },
            "status": {
                "pending": "Pending",
                "accepted": "Accepted",
                "completed": "Completed",
                "skipped": "Skipped",
                "cancelled": "Cancelled",
            },
            "noVolumeEstimate": "No volume estimate",
            "confidence": "Confidence",
            "source": "Source",
            "actualWater": "Water applied",
            "notRecorded": "Not recorded",
            "actualVolume": "Water applied (litres)",
            "actualDuration": "Duration (minutes)",
            "volumePlaceholder": "Litres applied",
            "durationPlaceholder": "Minutes",
            "saveActual": "Save actual",
            "accept": "Accept",
            "recordActual": "Record actual",
            "skip": "Skip",
            "skippedByFarmer": "Skipped by the farmer.",
            "planned": "Planned",
        },
        "model": {
            "status": {
                "baseline_only": "Baseline only",
                "provisional": "Provisional",
                "validated": "Validated",
            },
            "activePredictor": "Active predictor",
            "trainingSamples": "Training samples",
            "requiredSamples": "Required samples",
            "spanDays": "Span (days)",
        },
    },
    "hi": {
        "analytics": {
            "noMeasuredWater": "अभी तक कोई मापा गया सिंचाई जल मात्रा दर्ज नहीं है।",
            "dailyConsumptionChartLabel": "दैनिक सिंचाई जल उपभोग",
            "fieldUsageChartLabel": "प्रति खेत उपयोग किया गया जल",
            "cropUsageChartLabel": "प्रति फसल उपयोग किया गया जल",
            "plannedVsActualLabel": "नियोजित और वास्तविक सिंचाई जल",
            "trendChartLabel": "जल उपभोग की प्रवृत्ति",
            "noMoistureReadings": "इस अवधि में कोई मृदा नमी रीडिंग नहीं है।",
            "moistureTrendLabel": "मृदा नमी की प्रवृत्ति",
            "waterUsed": "उपयोग किया गया जल",
            "planned": "नियोजित",
            "actual": "वास्तविक",
            "noPlannedWater": "कोई नियोजित सिंचाई दर्ज नहीं है।",
            "moistureTrends": "मृदा नमी की प्रवृत्ति",
            "selectField": "खेत चुनें",
            "rangeLabel": "समय अवधि",
            "customRange": "कस्टम",
            "from": "से",
            "to": "तक",
            "bandFor": "लक्ष्य सीमा",
            "readingsShown": "दिखाई गई रीडिंग",
            "moistureTrendFor": "{{field}} की मृदा नमी की प्रवृत्ति",
            "showDataTable": "रीडिंग तालिका के रूप में दिखाएं",
            "gapNotice": "अनुपस्थित माप गैप के रूप में दिखते हैं। वर्डन्ट कभी दर्ज न की गई रीडिंग नहीं भरता।",
            "dailyConsumption": "दैनिक उपभोग",
            "weeklyTrend": "साप्ताहिक प्रवृत्ति",
            "monthlyTrend": "मासिक प्रवृत्ति",
            "fieldWiseUsage": "प्रति खेत उपयोग किया गया जल",
            "plannedVsActual": "नियोजित बनाम वास्तविक",
            "moistureStatusDistribution": "खेत स्थिति सारांश",
            "cropWiseUsage": "प्रति फसल उपयोग किया गया जल",
            "fieldsNeedingMeasurements": "नई माप की आवश्यकता वाले खेत",
            "allFieldsUpdated": "हर खेत की रीडिंग अद्यतन है।",
            "noIrrigationEvents": "अभी तक कोई सिंचाई घटना दर्ज नहीं है।",
            "dashboardFootnote": "चार्ट केवल मापे गए मानों पर आधारित हैं। नियोजित सिंचाई को उपयोगित जल नहीं गिना जाता।",
            "litresPerAcre": "लीटर प्रति एकड़",
            "averagePerEvent": "प्रत्येक सिंचाई औसत",
            "frequency": "सिंचाई की आवृत्ति",
            "previousPeriod": "पिछली अवधि",
            "currentPeriod": "वर्तमान अवधि",
            "totalWaterUsed": "कुल उपयोगित जल",
            "measuredEvents": "मापी गई घटनाएं",
            "unmeasuredEvents": "बिना माप की घटनाएं",
        },
        "schedule": {
            "title": "सिंचाई अनुसूची",
            "emptyTitle": "आज कोई सिंचाई निर्धारित नहीं है।",
            "emptyDescription": "फिलहाल किसी खेत को सिंचाई की आवश्यकता नहीं है। आवश्यकता होने पर वर्डन्ट सुझाव दिखाएगा।",
            "decisionSupportNotice": "यह अनुसूची निर्णय सहायता है। वर्डन्ट सिंचाई उपकरण नियंत्रित नहीं करता; यह आपकी निर्णय है कि सिंचाई कब और करें।",
            "priority": {
                "low": "कम",
                "medium": "मध्यम",
                "high": "अधिक",
                "critical": "गंभीर",
                "uncertain": "अनिश्चित",
            },
            "status": {
                "pending": "लंबित",
                "accepted": "स्वीकृत",
                "completed": "पूर्ण",
                "skipped": "छोड़ा गया",
                "cancelled": "रद्द",
            },
            "noVolumeEstimate": "कोई मात्रा अनुमान नहीं",
            "confidence": "विश्वास",
            "source": "स्रोत",
            "actualWater": "डाला गया जल",
            "notRecorded": "दर्ज नहीं",
            "actualVolume": "डाला गया जल (लीटर)",
            "actualDuration": "अवधि (मिनट)",
            "volumePlaceholder": "डाला गया लीटर",
            "durationPlaceholder": "मिनट",
            "saveActual": "वास्तविक सहेजें",
            "accept": "स्वीकार करें",
            "recordActual": "वास्तविक दर्ज करें",
            "skip": "छोड़ें",
            "skippedByFarmer": "किसान द्वारा छोड़ा गया।",
            "planned": "नियोजित",
        },
        "model": {
            "status": {
                "baseline_only": "केवल बेसलाइन",
                "provisional": "अस्थायी",
                "validated": "सत्यापित",
            },
            "activePredictor": "सक्रिय पूर्वानुमानकर्ता",
            "trainingSamples": "प्रशिक्षण नमूने",
            "requiredSamples": "आवश्यक नमूने",
            "spanDays": "अवधि (दिन)",
        },
    },
    "kn": {
        "analytics": {
            "noMeasuredWater": "ಇನ್ನೂ ಅಳೆದ ನೀರಾವರಿ ಪ್ರಮಾಣ ದಾಖಲಾಗಿಲ್ಲ.",
            "dailyConsumptionChartLabel": "ದೈನಂದಿನ ನೀರಾವರಿ ಬಳಕೆ",
            "fieldUsageChartLabel": "ಪ್ರತಿ ಹೊಲದ ಬಳಕೆ",
            "cropUsageChartLabel": "ಪ್ರತಿ ಬೆಳೆಯ ಬಳಕೆ",
            "plannedVsActualLabel": "ಯೋಜಿತ ಮತ್ತು ನಿಜವಾದ ನೀರಾವರಿ",
            "trendChartLabel": "ನೀರು ಬಳಕೆಯ ಪ್ರವೃತ್ತಿ",
            "noMoistureReadings": "ಈ ಅವಧಿಯಲ್ಲಿ ಮಣ್ಣಿನ ತೇವಾಂಶ ಓದುವಿಕೆ ಇಲ್ಲ.",
            "moistureTrendLabel": "ಮಣ್ಣಿನ ತೇವಾಂಶದ ಪ್ರವೃತ್ತಿ",
            "waterUsed": "ಬಳಸಿದ ನೀರು",
            "planned": "ಯೋಜಿತ",
            "actual": "ನಿಜವಾದ",
            "noPlannedWater": "ಯೋಜಿತ ನೀರಾವರಿ ದಾಖಲಾಗಿಲ್ಲ.",
            "moistureTrends": "ಮಣ್ಣಿನ ತೇವಾಂಶದ ಪ್ರವೃತ್ತಿ",
            "selectField": "ಹೊಲ ಆಯ್ಕೆಮಾಡಿ",
            "rangeLabel": "ಸಮಯ ವ್ಯಾಪ್ತಿ",
            "customRange": "ಕಸ್ಟಮ್",
            "from": "ಇಂದ",
            "to": "ಗೆ",
            "bandFor": "ಗುರಿ ವ್ಯಾಪ್ತಿ",
            "readingsShown": "ತೋರಿಸಿದ ಓದುವಿಕೆಗಳು",
            "moistureTrendFor": "{{field}} ನ ಮಣ್ಣಿನ ತೇವಾಂಶದ ಪ್ರವೃತ್ತಿ",
            "showDataTable": "ಓದುವಿಕೆಗಳನ್ನು ಕೋಷ್ಟಕವಾಗಿ ತೋರಿಸಿ",
            "gapNotice": "ಇಲ್ಲದ ಮಾಪನಗಳು ಅಂತರಗಳಾಗಿ ಕಾಣುತ್ತವೆ. ವರ್ಡನ್ಟ್ ದಾಖಲಾಗದ ಓದುವಿಕೆಯನ್ನು ಎಂದು ಮಾಡುವುದಿಲ್ಲ.",
            "dailyConsumption": "ದೈನಂದಿನ ಬಳಕೆ",
            "weeklyTrend": "ವಾರದ ಪ್ರವೃತ್ತಿ",
            "monthlyTrend": "ಮಾಸಿಕ ಪ್ರವೃತ್ತಿ",
            "fieldWiseUsage": "ಪ್ರತಿ ಹೊಲದ ಬಳಕೆ",
            "plannedVsActual": "ಯೋಜಿತ ಮತ್ತು ನಿಜವಾದ",
            "moistureStatusDistribution": "ಹೊಲದ ಸ್ಥಿತಿ ಸಾರಾಂಶ",
            "cropWiseUsage": "ಪ್ರತಿ ಬೆಳೆಯ ಬಳಕೆ",
            "fieldsNeedingMeasurements": "ಹೊಸ ಮಾಪನ ಅಗತ್ಯವಿರುವ ಹೊಲಗಳು",
            "allFieldsUpdated": "ಎಲ್ಲಾ ಹೊಲಗಳ ಓದುವಿಕೆ ನವೀನವಾಗಿದೆ.",
            "noIrrigationEvents": "ಇನ್ನೂ ಯಾವುದೇ ನೀರಾವರಿ ಘಟನೆ ದಾಖಲಾಗಿಲ್ಲ.",
            "dashboardFootnote": "ಚಾರ್ಟ್‌ಗಳು ಅಳೆದ ಮೌಲ್ಯಗಳ ಆಧಾರದ ಮೇಲೆ ಮಾತ್ರ. ಯೋಜಿತ ನೀರಾವರಿಯನ್ನು ಬಳಸಿದ ನೀರಿನಲ್ಲಿ ಎಣಿಸಲಾಗುವುದಿಲ್ಲ.",
            "litresPerAcre": "ಎಕರೆಗೆ ಲೀಟರ್",
            "averagePerEvent": "ಪ್ರತಿ ನೀರಾವರಿ ಸರಾಸರಿ",
            "frequency": "ನೀರಾವರಿ ಆವರ್ತನ",
            "previousPeriod": "ಹಿಂದಿನ ಅವಧಿ",
            "currentPeriod": "ಪ್ರಸ್ತುತ ಅವಧಿ",
            "totalWaterUsed": "ಒಟ್ಟು ಬಳಸಿದ ನೀರು",
            "measuredEvents": "ಅಳೆದ ಘಟನೆಗಳು",
            "unmeasuredEvents": "ಮಾಪನವಿಲ್ಲದ ಘಟನೆಗಳು",
        },
        "schedule": {
            "title": "ನೀರಾವರಿ ನಿಗದಿ",
            "emptyTitle": "ಇಂದು ಯಾವುದೇ ನೀರಾವರಿ ನಿಗದಿಪಡಿಸಿಲ್ಲ.",
            "emptyDescription": "ಪ್ರಸ್ತುತ ಯಾವ ಹೊಲಕ್ಕೂ ನೀರಾವರಿ ಅಗತ್ಯವಿಲ್ಲ. ಅಗತ್ಯವಿದ್ದಾಗ ವರ್ಡನ್ಟ್ ಸೂಚಿಸುತ್ತದೆ.",
            "decisionSupportNotice": "ಈ ನಿಗದಿ ನಿರ್ಧಾರ ಸಹಾಯವಾಗಿದೆ. ವರ್ಡನ್ಟ್ ನೀರಾವರಿ ಸಾಧನಗಳನ್ನು ನಿಯಂತ್ರಿಸುವುದಿಲ್ಲ; ಯಾವಾಗ ನೀರು ಹಾಕಬೇಕೆಂಬುದು ನಿಮ್ಮ ನಿರ್ಧಾರ.",
            "priority": {
                "low": "ಕಡಿಮೆ",
                "medium": "ಮಧ್ಯಮ",
                "high": "ಹೆಚ್ಚು",
                "critical": "ಗಂಭೀರ",
                "uncertain": "ಅನಿಶ್ಚಿತ",
            },
            "status": {
                "pending": "ಬಾಕಿ",
                "accepted": "ಸ್ವೀಕರಿಸಲಾಗಿದೆ",
                "completed": "ಪೂರ್ಣ",
                "skipped": "ಬಿಟ್ಟುಬಿಡಲಾಗಿದೆ",
                "cancelled": "ರದ್ದು",
            },
            "noVolumeEstimate": "ಪ್ರಮಾಣ ಅಂದಾಜಿಲ್ಲ",
            "confidence": "ವಿಶ್ವಾಸ",
            "source": "ಮೂಲ",
            "actualWater": "ಹಾಕಿದ ನೀರು",
            "notRecorded": "ದಾಖಲಾಗಿಲ್ಲ",
            "actualVolume": "ಹಾಕಿದ ನೀರು (ಲೀಟರ್)",
            "actualDuration": "ಅವಧಿ (ನಿಮಿಷ)",
            "volumePlaceholder": "ಲೀಟರ್ ಹಾಕಿದದ್ದು",
            "durationPlaceholder": "ನಿಮಿಷ",
            "saveActual": "ನಿಜವಾದ ಉಳಿಸಿ",
            "accept": "ಸ್ವೀಕರಿಸಿ",
            "recordActual": "ನಿಜವಾದ ದಾಖಲಾಸಿ",
            "skip": "ಬಿಟ್ಟುಬಿಡಿ",
            "skippedByFarmer": "ರೈತರು ಬಿಟ್ಟುಬಿಡಲಾಗಿದೆ.",
            "planned": "ಯೋಜಿತ",
        },
        "model": {
            "status": {
                "baseline_only": "ಕೇವಲ ಬೇಸ್‌ಲೈನ್",
                "provisional": "ತಾತ್ಕಾಲಿಕ",
                "validated": "ಪರಿಶೀಲಿತ",
            },
            "activePredictor": "ಸಕ್ರಿಯ ಮುನ್ಸೂಚಕ",
            "trainingSamples": "ತರಬೇತಿ ಮಾದರಿಗಳು",
            "requiredSamples": "ಅಗತ್ಯ ಮಾದರಿಗಳು",
            "spanDays": "ಅವಧಿ (ದಿನಗಳು)",
        },
    },
    "ta": {
        "analytics": {
            "noMeasuredWater": "இதுவரை அளவிடப்பட்ட பாசன நீர் தொகை பதிவாகவில்லை.",
            "dailyConsumptionChartLabel": "நீரின் தினையான நீர்ப்பாசனம்",
            "fieldUsageChartLabel": "தோட்டம் வாரியாக பயன்படுத்திய நீர்",
            "cropUsageChartLabel": "பயிர் வாரியாக பயன்படுத்திய நீர்",
            "plannedVsActualLabel": "திட்டமிடப்பட்ட மற்றும் உண்மையான பாசன நீர்",
            "trendChartLabel": "நீர் பயன்பாட்டின் போக்கு",
            "noMoistureReadings": "இந்தக் காலத்தில் மண் ஈரப்பதம் பதிவுகள் இல்லை.",
            "moistureTrendLabel": "மண் ஈரப்பதத்தின் போக்கு",
            "waterUsed": "பயன்படுத்திய நீர்",
            "planned": "திட்டமிடப்பட்டது",
            "actual": "உண்மையானது",
            "noPlannedWater": "திட்டமிடப்பட்ட பாசனம் பதிவாகவில்லை.",
            "moistureTrends": "மண் ஈரப்பத போக்கு",
            "selectField": "தோட்டத்தைத் தேர்ந்தெடுக்கவும்",
            "rangeLabel": "கால அளவு",
            "customRange": "தனிப்பயன்",
            "from": "முதல்",
            "to": "வரை",
            "bandFor": "இலக்கு வரம்பு",
            "readingsShown": "காட்டப்பட்ட பதிவுகள்",
            "moistureTrendFor": "{{field}} மண் ஈரப்பத போக்கு",
            "showDataTable": "பதிவுகளை அட்டவணையாகக் காட்டு",
            "gapNotice": "இல்லாத அளவீடுகள் இடைவெளியாகத் தெரியும். வெர்டென்ட் பதிவாகாத அளவீட்டை நிரப்புவதில்லை.",
            "dailyConsumption": "தினையான பயன்பாடு",
            "weeklyTrend": "வாராந்திர போக்கு",
            "monthlyTrend": "மாதாந்திர போக்கு",
            "fieldWiseUsage": "தோட்டம் வாரியான பயன்பாடு",
            "plannedVsActual": "திட்டமிடப்பட்டது மற்றும் உண்மையானது",
            "moistureStatusDistribution": "தோட்ட நிலை சுருக்கம்",
            "cropWiseUsage": "பயிர் வாரியான பயன்பாடு",
            "fieldsNeedingMeasurements": "புதிய அளவீடு தேவையான தோட்டங்கள்",
            "allFieldsUpdated": "அனைத்து தோட்டங்களின் பதிவுகளும் புதுமையானவை.",
            "noIrrigationEvents": "இதுவரை எந்த பாசன நிகழ்வும் பதிவாகவில்லை.",
            "dashboardFootnote": "சார்டுகள் அளவிடப்பட்ட மதிப்புகளை மட்டும் காட்டுகின்றன. திட்டமிடப்பட்ட பாசனம் பயன்படுத்திய நீராகக் கணக்கிடப்படாது.",
            "litresPerAcre": "ஏக்கரைக்கு லிட்டர்",
            "averagePerEvent": "ஒரு பாசனத்திற்கான சராசரி",
            "frequency": "பாசன அதிர்வெண்",
            "previousPeriod": "முந்தைய காலகட்டம்",
            "currentPeriod": "தற்போதைய காலகட்டம்",
            "totalWaterUsed": "மொத்தப் பயன்படுத்திய நீர்",
            "measuredEvents": "அளவிடப்பட்ட நிகழ்வுகள்",
            "unmeasuredEvents": "அளவீடு இல்லாத நிகழ்வுகள்",
        },
        "schedule": {
            "title": "பாசன அட்டவணை",
            "emptyTitle": "இன்று எந்த பாசனமும் திட்டமிடப்படவில்லை.",
            "emptyDescription": "தற்போது எந்தத் தோட்டத்திற்கும் பாசன தேவை இல்லை. தேவைப்பட்டால் வெர்டென்ட் பரிந்துரைக்கும்.",
            "decisionSupportNotice": "இந்த அட்டவணை முடிவு ஆதரவாகும். வெர்டென்ட் பாசன உபகரணங்களைக் கட்டுப்படுத்துவதில்லை; எப்போது நீர் ஊற வேண்டும் என்பது உங்கள் முடிவு.",
            "priority": {
                "low": "குறைவு",
                "medium": "நடுத்தரம்",
                "high": "அதிகம்",
                "critical": "ஆபத்தானது",
                "uncertain": "நிச்சயமற்றது",
            },
            "status": {
                "pending": "நிலுவையில்",
                "accepted": "ஏற்கப்பட்டது",
                "completed": "முடிந்தது",
                "skipped": "தவிர்க்கப்பட்டது",
                "cancelled": "ரத்து",
            },
            "noVolumeEstimate": "தொகை மதிப்பீடு இல்லை",
            "confidence": "நம்பிக்கை",
            "source": "மூலம்",
            "actualWater": "வழங்கிய நீர்",
            "notRecorded": "பதிவாகவில்லை",
            "actualVolume": "வழங்கிய நீர் (லிட்டர்)",
            "actualDuration": "நேரம் (நிமிடங்கள்)",
            "volumePlaceholder": "வழங்கிய லிட்டர்",
            "durationPlaceholder": "நிமிடங்கள்",
            "saveActual": "உண்மையைச் சேமி",
            "accept": "ஏற்கு",
            "recordActual": "உண்மையைப் பதிவி செய்",
            "skip": "தவிர்",
            "skippedByFarmer": "விவசாயி தவிர்த்தார்.",
            "planned": "திட்டமிடப்பட்டது",
        },
        "model": {
            "status": {
                "baseline_only": "அடிப்படை மட்டும்",
                "provisional": " provisional",
                "validated": "சரிபார்க்கப்பட்டது",
            },
            "activePredictor": "செயல்படும் முன்னறிஞ்சி",
            "trainingSamples": "பயிற்சி மாதிரிகள்",
            "requiredSamples": "தேவையான மாதிரிகள்",
            "spanDays": "கால அளவு (நாட்கள்)",
        },
    },
}

DASHBOARD_KEYS = {
    "en": {
        "overviewTitle": "Farm overview",
        "fieldsHealthy": "Healthy fields",
        "waterUsedToday": "Water used today",
        "scheduledVolumeToday": "Scheduled today",
        "scheduleTitle": "Today's irrigation schedule",
        "weatherImpactTitle": "Weather impact",
        "waterAnalyticsTitle": "Water consumption",
        "viewReports": "View reports",
        "insightsTitle": "Crop and field insights",
        "modelTransparencyTitle": "Prediction source",
    },
    "hi": {
        "overviewTitle": "खेत का अवलोकन",
        "fieldsHealthy": "स्वस्थ खेत",
        "waterUsedToday": "आज उपयोग किया गया जल",
        "scheduledVolumeToday": "आज निर्धारित",
        "scheduleTitle": "आज की सिंचाई अनुसूची",
        "weatherImpactTitle": "मौसम का प्रभाव",
        "waterAnalyticsTitle": "जल उपभोग",
        "viewReports": "रिपोर्ट देखें",
        "insightsTitle": "फसल और खेत की जानकारी",
        "modelTransparencyTitle": "पूर्वानुमान स्रोत",
    },
    "kn": {
        "overviewTitle": "ಹೊಲದ ಅವಲೋಕನ",
        "fieldsHealthy": "ಆರೋಗ್ಯಕರ ಹೊಲಗಳು",
        "waterUsedToday": "ಇಂದು ಬಳಸಿದ ನೀರು",
        "scheduledVolumeToday": "ಇಂದು ನಿಗದಿಪಡಿಸಿದ್ದು",
        "scheduleTitle": "ಇಂದಿನ ನೀರಾವರಿ ನಿಗದಿ",
        "weatherImpactTitle": "ಹವಾಮಾನದ ಪರಿಣಾಮ",
        "waterAnalyticsTitle": "ನೀರಿನ ಬಳಕೆ",
        "viewReports": "ವರದಿ ನೋಡಿ",
        "insightsTitle": "ಬೆಳೆ ಮತ್ತು ಹೊಲದ ಮಾಹಿತಿ",
        "modelTransparencyTitle": "ಮುನ್ಸೂಚನೆಯ ಮೂಲ",
    },
    "ta": {
        "overviewTitle": "பயிர் விவரம்",
        "fieldsHealthy": "ஆரோக்கியமான தோட்டங்கள்",
        "waterUsedToday": "இன்று பயன்படுத்திய நீர்",
        "scheduledVolumeToday": "இன்று திட்டமிடப்பட்டது",
        "scheduleTitle": "இன்றைய பாசன அட்டவணை",
        "weatherImpactTitle": "வானிலை தாக்கம்",
        "waterAnalyticsTitle": "நீர் பயன்பாடு",
        "viewReports": "அறிக்கைகளைப் பார்க்கவும்",
        "insightsTitle": "பயிர் மற்றும் தோட்ட அறிவு",
        "modelTransparencyTitle": "முன்னறிஞ்சல் மூலம்",
    },
}

WEATHER_KEYS = {
    "en": {
        "forecastTemperature": "Forecast temperature",
        "max": "Max",
        "min": "Min",
        "unavailableShort": "Weather data is not available right now.",
    },
    "hi": {
        "forecastTemperature": "अनुमानित तापमान",
        "max": "अधिकतम",
        "min": "न्यूनतम",
        "unavailableShort": "मौसम का डेटा अभी उपलब्ध नहीं है।",
    },
    "kn": {
        "forecastTemperature": "ಮುನ್ಸೂಚಿತ ತಾಪಮಾನ",
        "max": "ಗರಿಷ್ಠ",
        "min": "ಕನಿಷ್ಠ",
        "unavailableShort": "ಹವಾಮಾನದ ಮಾಹಿತಿ ಸದ್ಯಕ್ ಲಭ್ಯವಿಲ್ಲ.",
    },
    "ta": {
        "forecastTemperature": "முன்னறிஞ்சப்பட்ட வெப்பநிலை",
        "max": "அதிகம்",
        "min": "குறைந்தது",
        "unavailableShort": "வானிலை தரவு தற்போது கிடைக்கவில்லை.",
    },
}


def render(value, indent: int) -> str:
    pad = " " * indent
    if isinstance(value, dict):
        lines = ["{"]
        for key, item in value.items():
            rendered = render(item, indent + 2)
            lines.append(f"{pad}  {key}: {rendered},")
        lines.append(pad + "}")
        return "\n".join(lines)
    return f'"{value}"'


def insert_sections(path: Path, locale: str) -> None:
    text = path.read_text(encoding="utf-8")
    for name, section in SECTIONS[locale].items():
        if f"\n  {name}: {{" in text or f'\n  "{name}": {{' in text:
            continue
        block = f"\n  {name}: {render(section, 2)},"
        if "export default" in text:
            # Locale files that export a named object end with an export
            # statement, so the object literal has to be closed earlier.
            export_index = text.index("export default")
            close_index = text.rindex("}", 0, export_index)
            text = text[:close_index].rstrip() + block + "\n" + text[close_index:]
        else:
            text = text.rstrip()
            assert text.endswith("}")
            text = text[:-1].rstrip() + block + "\n}\n"
    path.write_text(text, encoding="utf-8")


def repair_missing_commas(path: Path) -> None:
    """Add the comma a preceding section needs when a new one follows it."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"\n  \}\n(  [A-Za-z\"'])", r"\n  },\n\1", text)
    path.write_text(text, encoding="utf-8")


def _find_section(text: str, name: str) -> int:
    """Return the index of a top-level section, quoted or unquoted."""
    for marker in (f"\n  {name}: {{", f'\n  "{name}": {{'):
        if marker in text:
            return text.index(marker) + 1
    raise ValueError(f"section {name} not found")


def insert_dashboard_keys(path: Path, locale: str) -> None:
    text = path.read_text(encoding="utf-8")
    index = _find_section(text, "dashboard")
    marker_end = text.index("{", index) + 1
    # Locale files that spread the English section must place their own keys
    # after the spread, otherwise English would win.
    spread = re.search(r"\n\s*\.\.\.en\.dashboard,", text[marker_end:])
    if spread:
        marker_end += spread.end()
    keys = DASHBOARD_KEYS[locale]
    additions = "".join(
        f"\n    {key}: \"{value}\"," for key, value in keys.items() if f"{key}:" not in text
    )
    if not additions:
        return
    text = text[:marker_end] + additions + text[marker_end:]
    path.write_text(text, encoding="utf-8")


def insert_weather_keys(path: Path, locale: str) -> None:
    text = path.read_text(encoding="utf-8")
    index = _find_section(text, "weather")
    marker_end = text.index("{", index) + 1
    spread = re.search(r"\n\s*\.\.\.en\.weather,", text[marker_end:])
    if spread:
        marker_end += spread.end()
    keys = WEATHER_KEYS[locale]
    additions = "".join(
        f"\n    {key}: \"{value}\"," for key, value in keys.items() if f"{key}:" not in text
    )
    if not additions:
        return
    text = text[:marker_end] + additions + text[marker_end:]
    path.write_text(text, encoding="utf-8")


def main() -> None:
    for locale in ("en", "hi", "kn", "ta"):
        path = TRANSLATIONS / f"{locale}.ts"
        insert_sections(path, locale)
        repair_missing_commas(path)
        insert_dashboard_keys(path, locale)
        insert_weather_keys(path, locale)
        print(f"updated {path}")


if __name__ == "__main__":
    main()
