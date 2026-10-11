"""User-facing copy for the Kabadi Khata bot.

Three languages, chosen per user at /start (a contextvar carries the choice so
the handlers don't pass it on every call):
  - "hi"      = Hinglish (romanized Hindi) — the default, easiest for low-literacy
                phone users to read.
  - "hi_dev"  = Hindi in Devanagari (हिंदी).
  - "en"      = English (README, demo, toggle).

Usage:
    from bot.strings_hi import t, set_lang, MATERIAL_LABELS
    t("welcome")                      # current contextvar language (default Hinglish)
    t("welcome", lang="en")           # explicit English
    set_lang("hi_dev"); t("welcome")  # Devanagari Hindi
"""
import contextvars

LANG_DEFAULT = "hi"            # "hi" = Hinglish, "hi_dev" = Devanagari Hindi, "en" = English
LANGS = ("hi", "hi_dev", "en")

HI = {
    "welcome": "Namaste! \U0001F64F Main *Kabadi Khata* hoon.\nAapke har collection ka pakka receipt banata hoon — bas photo kheencho, kaagaz-kaam main sambhal loonga.",
    "ask_name": "Pehle apna naam batao.",
    "name_saved": "Theek hai {name} ji! ✅",
    "ask_locality": "Aap kis ilaake mein kaam karte ho? Neeche se chuno \U0001F447",
    "locality_saved": "{locality} set ho gaya. ✅",
    "send_photo": "Ab taraazu (scale) aur maal ki ek photo bhejo \U0001F4F7",
    "after_photo": "Badhiya! Ab maal ka type aur weight batao —\nbutton dabao, ya voice note bhejo \U0001F3A4",
    "choose_material": "Maal kaun sa hai?",
    "enter_weight": "Kitne kilo? Number dabao.",
    "weight_prompt": "Weight (kg): {kg}",
    "processing": "Ek second... check kar raha hoon ✅",
    "receipt_ready": "Receipt ready! ✅ Yeh raha aapka pakka hisaab.",
    "question_prefix": "\U0001F914 ",  # agent's follow-up question is appended after this
    "answer_hint": "Sahi jawaab button se chuno ya dobara batao.",
    "hisaab_button": "\U0001F4CA Mera Hisaab",
    "hisaab_summary": (
        "\U0001F4CA *Mera Hisaab* — {name}\n\n"
        "Aaj: {today_kg} kg • ₹{today_inr}\n"
        "Is mahine: {month_kg} kg • ₹{month_inr}\n"
        "Total receipts: {count}\n"
        "✅ Chain verified"
    ),
    "help": "Photo bhejo → maal ka type aur kg batao → receipt milega. /hisaab se apna total dekho.",
    "error_generic": "Arre, kuch gadbad ho gayi. Dobara try karo. \U0001F647",
    "synthetic_notice": "(Demo data — asli collection nahi)",
    "btn_voice": "\U0001F3A4 Voice note",
    "btn_tap": "⌨️ Button se batao",
    "btn_yes": "Haan",
    "btn_no": "Nahi",
    "btn_confirm": "Pakka ✅",
    "btn_cancel": "Cancel",
    "btn_retry": "Dobara batao",
    "need_start": "Pehle /start karke naam aur ilaaka set karo.",
    "voice_soon": "Voice support aa raha hai — abhi button se batao.",
    "bad_weight": "Weight theek nahi laga. Dobara daalo (0–500 kg).",
    "cancelled": "Theek hai, cancel kar diya.",
    "demo_on": "Demo ON: agent taraazu par 12 kilo 'dekhega'. Alag weight daalo (jaise 20) to woh refuse karega.",
    "demo_off": "Demo OFF. Ab asli photo se collection hoga.",
    "choose_language": "Bhasha chuno:",
}

HI_DEV = {
    "welcome": "नमस्ते! \U0001F64F मैं *कबाड़ी खाता* हूँ।\nआपके हर कलेक्शन की पक्की रसीद बनाता हूँ — बस फ़ोटो खींचो, कागज़-काम मैं संभाल लूँगा।",
    "ask_name": "पहले अपना नाम बताओ।",
    "name_saved": "ठीक है {name} जी! ✅",
    "ask_locality": "आप किस इलाके में काम करते हो? नीचे से चुनो \U0001F447",
    "locality_saved": "{locality} सेट हो गया। ✅",
    "send_photo": "अब तराज़ू (स्केल) और माल की एक फ़ोटो भेजो \U0001F4F7",
    "after_photo": "बढ़िया! अब माल का टाइप और वज़न बताओ —\nबटन दबाओ, या वॉइस नोट भेजो \U0001F3A4",
    "choose_material": "माल कौन सा है?",
    "enter_weight": "कितने किलो? नंबर दबाओ।",
    "weight_prompt": "वज़न (किलो): {kg}",
    "processing": "एक सेकंड... चेक कर रहा हूँ ✅",
    "receipt_ready": "रसीद तैयार! ✅ ये रहा आपका पक्का हिसाब।",
    "question_prefix": "\U0001F914 ",
    "answer_hint": "सही जवाब बटन से चुनो या दोबारा बताओ।",
    "hisaab_button": "\U0001F4CA मेरा हिसाब",
    "hisaab_summary": (
        "\U0001F4CA *मेरा हिसाब* — {name}\n\n"
        "आज: {today_kg} किलो • ₹{today_inr}\n"
        "इस महीने: {month_kg} किलो • ₹{month_inr}\n"
        "कुल रसीदें: {count}\n"
        "✅ चेन वेरिफाइड"
    ),
    "help": "फ़ोटो भेजो → माल का टाइप और किलो बताओ → रसीद मिलेगी। /hisaab से अपना टोटल देखो।",
    "error_generic": "अरे, कुछ गड़बड़ हो गई। दोबारा कोशिश करो। \U0001F647",
    "synthetic_notice": "(डेमो डेटा — असली कलेक्शन नहीं)",
    "btn_voice": "\U0001F3A4 वॉइस नोट",
    "btn_tap": "⌨️ बटन से बताओ",
    "btn_yes": "हाँ",
    "btn_no": "नहीं",
    "btn_confirm": "पक्का ✅",
    "btn_cancel": "कैंसिल",
    "btn_retry": "दोबारा बताओ",
    "need_start": "पहले /start करके नाम और इलाका सेट करो।",
    "voice_soon": "वॉइस सपोर्ट आ रहा है — अभी बटन से बताओ।",
    "bad_weight": "वज़न ठीक नहीं लगा। दोबारा डालो (0–500 किलो)।",
    "cancelled": "ठीक है, कैंसिल कर दिया।",
    "demo_on": "डेमो ऑन: एजेंट तराज़ू पर 12 किलो 'देखेगा'। अलग वज़न डालो (जैसे 20) तो वो मना कर देगा।",
    "demo_off": "डेमो ऑफ। अब असली फ़ोटो से कलेक्शन होगा।",
    "choose_language": "भाषा चुनें:",
}

EN = {
    "welcome": "Hello! \U0001F64F I'm *Kabadi Khata*.\nI make a verified receipt for every collection — just send a photo and I'll handle the paperwork.",
    "ask_name": "First, tell me your name.",
    "name_saved": "Okay {name}! ✅",
    "ask_locality": "Which area do you work in? Pick below \U0001F447",
    "locality_saved": "{locality} set. ✅",
    "send_photo": "Now send one photo of the scale and the material \U0001F4F7",
    "after_photo": "Great! Now tell me the material and weight —\ntap the buttons, or send a voice note \U0001F3A4",
    "choose_material": "What material is it?",
    "enter_weight": "How many kg? Tap the number.",
    "weight_prompt": "Weight (kg): {kg}",
    "processing": "One second... checking ✅",
    "receipt_ready": "Receipt ready! ✅ Here is your verified record.",
    "question_prefix": "\U0001F914 ",
    "answer_hint": "Pick the correct answer or tell me again.",
    "hisaab_button": "\U0001F4CA My Account",
    "hisaab_summary": (
        "\U0001F4CA *My Account* — {name}\n\n"
        "Today: {today_kg} kg • ₹{today_inr}\n"
        "This month: {month_kg} kg • ₹{month_inr}\n"
        "Total receipts: {count}\n"
        "✅ Chain verified"
    ),
    "help": "Send a photo → tell me the material and kg → get a receipt. Use /hisaab for your totals.",
    "error_generic": "Sorry, something went wrong. Please try again. \U0001F647",
    "synthetic_notice": "(Demo data — not a real collection)",
    "btn_voice": "\U0001F3A4 Voice note",
    "btn_tap": "⌨️ Use buttons",
    "btn_yes": "Yes",
    "btn_no": "No",
    "btn_confirm": "Confirm ✅",
    "btn_cancel": "Cancel",
    "btn_retry": "Tell me again",
    "need_start": "Please /start first to set your name and area.",
    "voice_soon": "Voice support is coming — please use the buttons for now.",
    "bad_weight": "That weight doesn't look right. Enter again (0-500 kg).",
    "cancelled": "Okay, cancelled.",
    "demo_on": "Demo ON: the agent will 'see' 12 kg on the scale. Enter a different weight (e.g. 20) to make it refuse.",
    "demo_off": "Demo OFF. Collections now use the real photo.",
    "choose_language": "Choose your language:",
}

_TABLES = {"hi": HI, "hi_dev": HI_DEV, "en": EN}

# Material labels shown on the tap-button grid.
MATERIAL_LABELS = {
    "PET":           {"hi": "Plastic bottle", "hi_dev": "प्लास्टिक बोतल",   "en": "Plastic bottle (PET)"},
    "HDPE":          {"hi": "Hard plastic",   "hi_dev": "सख्त प्लास्टिक",    "en": "Hard plastic (HDPE)"},
    "LDPE_film":     {"hi": "Polythene/film", "hi_dev": "पॉलीथीन/फिल्म",    "en": "Polythene / film"},
    "mixed_plastic": {"hi": "Mixed plastic",  "hi_dev": "मिक्स प्लास्टिक",   "en": "Mixed plastic"},
    "cardboard":     {"hi": "Gatta/carton",   "hi_dev": "गत्ता/कार्टन",      "en": "Cardboard / carton"},
    "paper":         {"hi": "Raddi/kaagaz",   "hi_dev": "रद्दी/कागज़",       "en": "Paper / newspaper"},
    "metal":         {"hi": "Loha/metal",     "hi_dev": "लोहा/मेटल",         "en": "Metal"},
    "ewaste":        {"hi": "E-waste",        "hi_dev": "ई-कचरा",            "en": "E-waste"},
    "unknown":       {"hi": "Pata nahi",      "hi_dev": "पता नहीं",          "en": "Unknown"},
}

# Material order for the button grid.
MATERIAL_ORDER = ["PET", "HDPE", "LDPE_film", "mixed_plastic", "cardboard", "paper", "metal", "ewaste"]

# Per-task current language (set from the user's choice; isolated per async handler).
_current_lang = contextvars.ContextVar("kk_lang", default=LANG_DEFAULT)


def set_lang(lang: str) -> None:
    """Set the current task's language (ignores an unknown code, keeping the default)."""
    _current_lang.set(lang if lang in LANGS else LANG_DEFAULT)


def current_lang() -> str:
    return _current_lang.get()


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """Return a string by key in the chosen language, formatted with kwargs.

    ``lang=None`` uses the current contextvar language. Falls back to English, then
    to the key itself, so a missing key never crashes the bot.
    """
    if lang is None:
        lang = _current_lang.get()
    table = _TABLES.get(lang, HI)
    s = table.get(key)
    if s is None:
        s = EN.get(key, key)
    return s.format(**kwargs) if kwargs else s


def material_label(material: str, lang: str | None = None) -> str:
    """Display label for a material code in the chosen language; falls back to the code."""
    if lang is None:
        lang = _current_lang.get()
    entry = MATERIAL_LABELS.get(material)
    if entry is None:
        return material
    return entry.get(lang, entry.get("en", material))
