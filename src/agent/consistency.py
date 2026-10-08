"""Deterministic consistency rules. Code decides; the LLM never overrides this.

Returns every failing reason, plus ONE Hindi follow-up Question for the first (most important) failure.
"""
from __future__ import annotations

import math
from typing import Optional

from common.models import ConsistencyResult, PhashResult, PhotoRead

KG_TOLERANCE = 0.10          # claimed kg must be within ±10% of the scale reading
MIN_CONFIDENCE = 0.60        # below this, ask for a clearer photo
MAX_KG = 500.0
KG_EPSILON = 1e-9            # float noise guard so exactly ±10% passes (12 vs 10.8)

MATERIAL_GROUP = {
    "PET": "plastic", "HDPE": "plastic", "LDPE_film": "plastic", "mixed_plastic": "plastic",
    "cardboard": "paper", "paper": "paper", "metal": "metal", "ewaste": "ewaste", "unknown": "unknown",
}

MATERIAL_HI = {
    "PET": "प्लास्टिक बोतल (PET)", "HDPE": "सख़्त प्लास्टिक (HDPE)", "LDPE_film": "पन्नी",
    "mixed_plastic": "मिला-जुला प्लास्टिक", "cardboard": "गत्ता", "paper": "रद्दी काग़ज़",
    "metal": "लोहा/धातु", "ewaste": "ई-कचरा", "unknown": "अनजान माल",
}


def _kg(x: float) -> str:
    return f"{x:g}"


def check_consistency(
    photo: PhotoRead,
    phash: PhashResult,
    claimed_kg: Optional[float],
    claimed_material: Optional[str],
) -> ConsistencyResult:
    reasons: list[str] = []
    warnings: list[str] = []
    questions: list[str] = []

    def fail(reason: str, question_hi: str) -> None:
        reasons.append(reason)
        questions.append(question_hi)

    retake = "तराज़ू का नंबर साफ़ नहीं दिख रहा। कृपया तराज़ू की साफ़ फ़ोटो फिर से भेजिए।"
    if photo.kg is None:
        fail("scale_unreadable", retake)
    elif not photo.confidence >= MIN_CONFIDENCE:  # also catches NaN
        fail("low_confidence", retake)
    elif not (0 < photo.kg <= MAX_KG):
        fail("weight_out_of_range", f"तराज़ू पर {_kg(photo.kg)} किलो दिख रहा है, यह सही नहीं लगता। कृपया फिर से तौलकर फ़ोटो भेजिए।")

    if phash.is_duplicate:
        fail("duplicate_photo", "यह फ़ोटो पहले भी भेजी जा चुकी है। कृपया इस माल की नई फ़ोटो भेजिए।")

    if photo.kg is not None and not reasons:
        if claimed_kg is None:
            fail("no_claim", f"तराज़ू पर {_kg(photo.kg)} किलो दिख रहा है। क्या यह सही है?")
        elif not math.isfinite(claimed_kg) or claimed_kg <= 0:
            fail("claim_invalid", "आपने जो किलो बताया वह सही नहीं लगता। कृपया सही वज़न बताइए।")
        elif abs(claimed_kg - photo.kg) > KG_TOLERANCE * photo.kg + KG_EPSILON:
            fail("kg_mismatch", f"तराज़ू {_kg(photo.kg)} किलो दिखा रहा है, आपने {_kg(claimed_kg)} किलो बताया। कौन सा सही है?")

    if claimed_material and not reasons:
        if photo.material == "unknown":
            warnings.append("material_unverified")
        elif MATERIAL_GROUP[claimed_material] != MATERIAL_GROUP[photo.material]:
            fail(
                "material_mismatch",
                f"फ़ोटो में {MATERIAL_HI[photo.material]} दिख रहा है, आपने {MATERIAL_HI[claimed_material]} बताया। कौन सा सही है?",
            )

    if photo.kg is not None and not reasons and photo.material == "unknown" and not claimed_material:
        fail("material_unknown", "माल की पहचान फ़ोटो से नहीं हुई। कृपया बताइए कि यह कौन सा माल है।")

    return ConsistencyResult(
        ok=not reasons, reasons=reasons, warnings=warnings, question_hi=questions[0] if questions else None
    )
