"""Pull a Stated weight and a material out of a Hindi / Hinglish sentence, in code.

Handles digits ("12 kg", "12.5 किलो"), Hindi and Hinglish number words ("baara kilo",
"बारह किलो"), and the fraction words kabadiwalas use: dedh (1.5), dhai (2.5), saadhe X (X + 0.5),
sawa X (X + 0.25), paune X (X - 0.25). Used by transcribe() to cross-check the model and as a
fallback when the model gives no number. The sentence is data, never an instruction.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

_UNITS = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6, "chhah": 6,
    "che": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11, "gyaarah": 11, "barah": 12,
    "baarah": 12, "bara": 12, "baara": 12, "terah": 13, "tera": 13, "chaudah": 14, "chauda": 14,
    "pandrah": 15, "pandra": 15, "solah": 16, "sola": 16, "satrah": 17, "satra": 17, "atharah": 18,
    "athara": 18, "unnis": 19, "bees": 20, "bis": 20, "pachees": 25, "pachchis": 25, "pachis": 25,
    "tees": 30, "chalees": 40, "chalis": 40, "pachaas": 50, "pachas": 50, "saath": 60, "sattar": 70,
    "assi": 80, "nabbe": 90,
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "छह": 6, "छः": 6, "सात": 7, "आठ": 8,
    "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "सोलह": 16,
    "सत्रह": 17, "अठारह": 18, "उन्नीस": 19, "बीस": 20, "पच्चीस": 25, "तीस": 30, "चालीस": 40,
    "पचास": 50, "साठ": 60, "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
}
_STANDALONE = {"dedh": 1.5, "dedhh": 1.5, "dhai": 2.5, "dhaai": 2.5, "ढाई": 2.5, "डेढ़": 1.5, "डेढ": 1.5}
_MODIFIERS = {"saadhe": 0.5, "sade": 0.5, "saade": 0.5, "साढ़े": 0.5, "साढे": 0.5,
              "sawa": 0.25, "savaa": 0.25, "sava": 0.25, "सवा": 0.25,
              "paune": -0.25, "पौने": -0.25}
_KG_WORDS = r"(?:kg|kgs|kilo|kilos|kilogram|किलो|केजी)"
_HUNDRED = {"sau", "सौ"}

# Order matters: named materials (gatta, raddi) before generic container words (dabba, balti)
_MATERIALS = [
    ("PET", ["pet", "bottle", "botal", "बोतल", "bisleri", "बिसलेरी"]),
    ("LDPE_film", ["panni", "polythene", "polithin", "pannee", "पन्नी", "पॉलीथीन", "thaili", "थैली"]),
    ("cardboard", ["gatta", "gatte", "गत्ता", "गत्ते", "cardboard", "carton", "कार्टन", "कार्डबोर्ड"]),
    ("paper", ["raddi", "akhbaar", "akhbar", "newspaper", "kagaz", "kaagaz", "रद्दी", "अख़बार", "अखबार", "काग़ज़", "कागज"]),
    ("HDPE", ["hdpe", "dabba", "dabbe", "डिब्बा", "डिब्बे", "balti", "बाल्टी"]),
    ("metal", ["loha", "lohe", "लोहा", "लोहे", "tin", "टिन", "metal", "aluminium", "steel", "स्टील", "can", "cans",
               "एल्युमिनियम", "एल्यूमीनियम", "कैन", "bartan", "bartano", "बर्तन", "मेटल"]),
    ("ewaste", ["charger", "wire", "taar", "तार", "mobile", "battery", "e-waste", "ewaste", "चार्जर", "मोबाइल", "बैटरी"]),
    ("mixed_plastic", ["plastic", "प्लास्टिक", "plastik"]),
]


_NUKTA = "़"


def _norm(word: str) -> str:
    """Lower-case and drop the nukta dot, so कागज़ / कागज and अख़बार / अखबार match."""
    return unicodedata.normalize("NFD", word).lower().replace(_NUKTA, "")


def _tokens(text: str) -> list[str]:
    return re.findall(r"[\wऀ-ॿ.]+", _norm(text))


def stated_kg(text: str) -> Optional[float]:
    """The weight mentioned just before a kg word, or None. Digits win over words."""
    t = (text or "").lower()
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*" + _KG_WORDS, t)
    if m:
        return float(m.group(1).replace(",", "."))
    toks = _tokens(t)
    for i, tok in enumerate(toks):
        if not re.fullmatch(_KG_WORDS, tok):
            continue
        value = _number_before(toks, i)
        if value is not None:
            return value
    return None


_UNITS = {_norm(k): v for k, v in _UNITS.items()}
_STANDALONE = {_norm(k): v for k, v in _STANDALONE.items()}
_MODIFIERS = {_norm(k): v for k, v in _MODIFIERS.items()}
_HUNDRED = {_norm(k) for k in _HUNDRED}


def _number_before(toks: list[str], i: int) -> Optional[float]:
    if i == 0:
        return None
    prev = toks[i - 1]
    if re.fullmatch(r"\d+(?:\.\d+)?", prev):
        return float(prev)
    if prev in _STANDALONE:
        return _STANDALONE[prev]
    if prev in _HUNDRED:  # "paanch sau kilo" = 500, "dhai sau" = 250, "sau kilo" = 100
        base = _number_before(toks, i - 1)
        return base * 100 if base is not None else 100.0
    if prev in _UNITS:
        value = float(_UNITS[prev])
        if i >= 2 and toks[i - 2] in _MODIFIERS:
            value += _MODIFIERS[toks[i - 2]]
        return value
    return None


def stated_material(text: str) -> Optional[str]:
    """The first material word in the sentence, mapped to a Material, or None."""
    toks = set(_tokens(text or ""))
    for material, words in _MATERIALS:
        if any(_norm(w) in toks for w in words):
            return material
    return None
