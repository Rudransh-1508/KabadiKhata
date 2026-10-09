"""Run two Collections through the agent and print the tool-call trace.

    MOCK_LLM=1 python -m agent.demo          (from src/, or with src on PYTHONPATH)
"""
from __future__ import annotations

import base64

from agent.agent import handle_collection
from agent.fakes import InMemoryReceiptStore
from common.models import CollectionRequest, Taps


def b64(s: str) -> str:
    return base64.b64encode(s.encode()).decode()


def main() -> None:
    store = InMemoryReceiptStore()
    cases = [
        ("Pass: scale 12 kg PET, Raju taps 12 kg PET",
         CollectionRequest(collector_id="raju", photo_b64=b64("fixture:12:PET:0.92"),
                           taps=Taps(material="PET", kg=12), locality="Seelampur")),
        ("Mismatch: scale 12 kg, Raju taps 20 kg",
         CollectionRequest(collector_id="raju", photo_b64=b64("fixture:12:PET:0.92:second-load"),
                           taps=Taps(material="PET", kg=20), locality="Seelampur")),
    ]
    for title, req in cases:
        print(f"\n=== {title} ===")
        result = handle_collection(req, store, print_trace=True)
        if result.status == "receipt":
            r = result.receipt
            print(f"-> RECEIPT {r.receipt_id}  {r.weight_kg} kg {r.material}  seq={r.seq}  hash={r.hash[:12]}")
        else:
            print(f"-> QUESTION {result.question_hi}  reasons={result.reasons}")


if __name__ == "__main__":
    main()
