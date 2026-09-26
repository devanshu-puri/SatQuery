"""Small, offline multilingual front door for SatQuery analysis requests.

It deliberately has no model download or cloud dependency.  The parser only decides
workflow and display language; all measurements still come from the selected raster tool.
"""

import re
from typing import Any, Dict


LANGUAGES = {
    "hi": ("Hindi", r"[\u0900-\u097f]"),
    "bn": ("Bengali", r"[\u0980-\u09ff]"),
    "ta": ("Tamil", r"[\u0b80-\u0bff]"),
    "te": ("Telugu", r"[\u0c00-\u0c7f]"),
    "kn": ("Kannada", r"[\u0c80-\u0cff]"),
    "ml": ("Malayalam", r"[\u0d00-\u0d7f]"),
    "ar": ("Arabic", r"[\u0600-\u06ff]"),
}

TERM_HINTS = {
    "water": ("water", "lake", "river", "flood", "जल", "पानी", "पाण्य", "నీరు", "நீர்", "ನೀರು", "জল"),
    "vegetation": ("vegetation", "forest", "tree", "crop", "agriculture", "farm", "वन", "फसल", "खेती", "ಅರಣ್ಯ", "ಬೆಳೆ", "காடு", "பயிர", "పంట", "অরণ্য"),
    "built_up": ("built", "building", "urban", "road", "settlement", "city", "निर्म", "शहर", "इमारत", "ನಗರ", "ಕಟ್ಟಡ", "நகர", "கட்டிட", "నగర", "ভবন"),
    "change": ("change", "changed", "compare", "before", "after", "difference", "increase", "decrease", "बदल", "पहले", "बाद", "మార్పు", "ముందు", "తర్వాత", "மாற்ற", "முன்", "பின்", "ಬದಲ", "ಮೊದಲು", "ನಂತರ", "পরিবর্তন"),
    "sar": ("sar", "radar", "fusion", "backscatter", "optical and radar", "रडार", "ರಾಡಾರ್", "ரேடார்", "రాడార్"),
    "locate": ("where", "show", "highlight", "locate", "find", "outline", "mask", "map", "कहाँ", "दिखा", "नक्श", "ಎಲ್ಲಿ", "ತೋರ", "ನಕ್ಷ", "எங்கே", "காட்டு", "வரைபட", "ఎక్కడ", "చూప", "మ్యాప్", "কোথা", "দেখা"),
}


def interpret_query(query: str) -> Dict[str, Any]:
    text = (query or "").strip()
    lowered = text.lower()
    language = "en"
    language_name = "English"
    for code, (name, pattern) in LANGUAGES.items():
        if re.search(pattern, text):
            language, language_name = code, name
            break

    matched = {
        label for label, terms in TERM_HINTS.items()
        if any(term.lower() in lowered for term in terms)
    }
    if "sar" in matched:
        intent = "optical_sar_fusion"
    elif "change" in matched:
        intent = "bitemporal_change"
    elif "locate" in matched:
        intent = "region_grounding"
    else:
        intent = "single_image_vqa"

    target = next((label for label in ("water", "vegetation", "built_up") if label in matched), "land_cover")
    # English hints give deterministic classical tools a language-neutral request.
    routing_hints = " ".join(sorted(matched | {target}))
    return {
        "original_query": text,
        "language": language,
        "language_name": language_name,
        "intent": intent,
        "target_concept": target,
        "routing_hints": routing_hints,
    }


def localized_summary(language: str, task_type: str, stats: Dict[str, Any], fallback: str) -> str:
    """Return a concise, measured summary. Unsupported scripts retain the source response."""
    water = stats.get("sar_water_coverage_pct", stats.get("water_pct"))
    vegetation = stats.get("vegetation_pct")
    built = stats.get("built_up_pct")
    change = stats.get("change_percentage")
    if language == "en":
        return fallback
    values = ", ".join(
        item for item in (
            f"water {water}%" if water is not None else None,
            f"vegetation {vegetation}%" if vegetation is not None else None,
            f"built-up {built}%" if built is not None else None,
            f"surface change {change}%" if change is not None else None,
        ) if item
    ) or "the requested feature was analysed from the selected imagery"
    templates = {
        "hi": f"चुने गए उपग्रह चित्र का विश्लेषण पूरा हुआ। माप: {values}। नीचे तकनीकी विवरण और मानचित्र प्रमाण देखें।",
        "bn": f"নির্বাচিত স্যাটেলাইট চিত্রের বিশ্লেষণ সম্পন্ন। পরিমাপ: {values}। নিচে প্রযুক্তিগত বিবরণ ও মানচিত্র প্রমাণ দেখুন।",
        "ta": f"தேர்ந்தெடுத்த செயற்கைக்கோள் படத்தின் பகுப்பாய்வு முடிந்தது. அளவீடுகள்: {values}. கீழே தொழில்நுட்ப விவரங்களையும் வரைபட ஆதாரத்தையும் பார்க்கவும்.",
        "te": f"ఎంచుకున్న ఉపగ్రహ చిత్ర విశ్లేషణ పూర్తైంది. కొలతలు: {values}. క్రింద సాంకేతిక వివరాలు మరియు మ్యాప్ ఆధారాన్ని చూడండి.",
        "kn": f"ಆಯ್ಕೆ ಮಾಡಿದ ಉಪಗ್ರಹ ಚಿತ್ರದ ವಿಶ್ಲೇಷಣೆ ಪೂರ್ಣಗೊಂಡಿದೆ. ಅಳತೆಗಳು: {values}. ಕೆಳಗೆ ತಾಂತ್ರಿಕ ವಿವರಗಳು ಮತ್ತು ನಕ್ಷೆ ಸಾಕ್ಷ್ಯವನ್ನು ನೋಡಿ.",
        "ml": f"തിരഞ്ഞെടുത്ത ഉപഗ്രഹ ചിത്രത്തിന്റെ വിശകലനം പൂർത്തിയായി. അളവുകൾ: {values}. താഴെ സാങ്കേതിക വിവരങ്ങളും മാപ്പ് തെളിവും കാണുക.",
        "ar": f"اكتمل تحليل صورة القمر الصناعي المحددة. القياسات: {values}. راجع التفاصيل التقنية ودليل الخريطة أدناه.",
    }
    return templates.get(language, fallback)
