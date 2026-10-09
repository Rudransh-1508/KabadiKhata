# Spec review: p2-5-docs

Reviewed against CLAUDE.md, CONTEXT.md, `src/api/app.py`, `src/policy/*`, `src/radar/rules.py`, `src/radar/explain.py`, `src/common/config.py`, `src/agent/README.md`, `Makefile`, `tests/`. Read-only review of the code as it is now (an earlier review of this spec predates fixes that have since landed; this one supersedes it).

## Findings, most severe first

### 1. HIGH: the spec says 5 policies; the file has 8, so its own drift test would fail
`src/policy/policies.cedar` declares `kabadiwala-own-data`, `brand-own-certificates`, `auditor-oversight`, `kabadiwala-photo`, `kabadiwala-list-directory`, `self-registration`, `agent-create-receipt`, `agent-forbidden`. The spec listed 5 rows and also required "every `@id` in the file appears in the doc". The acceptance criterion "(5 rows)" is wrong.
**Decision: applied.** Table is 8 rows, one per `@id`; the criterion no longer hard-codes a count (the drift test is the check).

### 2. HIGH: Behaviours 6 and 7 describe defects that are already fixed in the code
`rules._explain` already calls `with_llm_explanation(flag)`. `register`, `list_actors`, `read_flags` and the `Directory`/`Actor` resource types are already in the schema and permitted (`auditor-oversight`, `kabadiwala-list-directory`, `self-registration`). Following the spec literally would have the implementer "fix" working code or invent changes. What is genuinely missing is the regression test (`tests/test_api.py` only calls `/radar/run`, no test asserts non-empty explanations).
**Decision: applied.** Behaviours 6 and 7 become "verify, then add only what is missing": add `test_radar_run_explains_flags`; run `tests/test_api.py` to confirm the three routes work; touch `src/radar/rules.py` and `src/policy/*` only if a check actually fails. Out-of-scope and acceptance lists updated, "compatibility change" reporting is conditional.

### 3. MEDIUM: route/action table incomplete
`src/api/app.py` also requires `read_receipt_pii` on `GET /photos/{sha}.jpg`, `search_receipts` on `GET /search/receipts` and `read_analytics` on `GET /analytics/tonnage`; `GET /certificates` and `POST /flags/{id}/decision` are also routes. `issue_certificate` is in the schema but has no route (only the Agent `forbid`). The spec's list of ten actions omitted three.
**Decision: applied.** Table lists all 13 route actions; `issue_certificate` noted as declared-and-forbidden-for-Agent only. Drift test now checks every `require(..., "<action>"` in `src/api/app.py` appears in the doc.

### 4. MEDIUM: env table incomplete and drift-prone
Code also reads `KK_PHOTO_DIR`, `KK_OPENSEARCH_URL`, `KK_OPENSEARCH_INDEX`, `KK_R1_THRESHOLD`, `KK_R2_MAX_DISTANCE`. Doc should not be a full env reference (P3's docs own the API ones).
**Decision: applied (partly).** Env table covers P2-relevant variables only; it links P3's `src/api/README.md` for API/search variables. `KK_R1_THRESHOLD`/`KK_R2_MAX_DISTANCE` (radar, P2-adjacent) are added. Test still checks each documented var is read by code.

### 5. MEDIUM: beat 4 depends on data that is not in this repo
`data/` is generated, absent in this worktree; `make seed` needs P1's world file. `src/ledger/world.py` is the built-in demo world.
**Decision: applied.** Spec already says use ids from `src/ledger/world.py` or placeholders with the pytest fallback; sharpened: the recorder lists ids via `GET /actors` and the Brand's Certificates via `GET /certificates?brand_id=`, and the doc must not state an id it did not read from `src/ledger/world.py`.

### 6. MEDIUM: security wording
Spec text could imply Cedar independently verifies the consistency check. `agent-create-receipt` trusts a `consistency_ok` context that our code supplies. Spec already says "policy layer that holds even if the agent code changes" and limitation (g). Also `X-Principal` is spoofable (limitation f).
**Decision: rejected (no change):** both are already required. One addition applied: the doc must not say a Brand or Kabadiwala "cannot" see data without the qualifier "under `X-Principal` stand-in auth".

### 7. LOW: `make` targets and tests
Makefile also has `sam-invoke`, `up`, `down`, `reindex`; the spec said only six exist. All exist, so naming them is fine; bot/console targets are absent.
**Decision: applied.** Behaviour 9 says "only targets present in `Makefile`", without a closed list that would go stale; the test is the guard.

### 8. LOW: `test_docs_have_no_forbidden_text` and path test fragility
Path regex must ignore `data/` and handle backticked paths with line suffixes or trailing punctuation; also `research/` links must exist.
**Decision: applied** (one clause in the test plan).

### 9. LOW: scope and length
~250 lines is a soft target; optional injection snippet is extra but small and tied to beat 1 ("refusal"). Docs are only needed for what the video shows.
**Decision: rejected (no change).** Snippet stays optional.

### 10. Vocabulary
Collection, Receipt, Question, Chain, Certificate, Flag, Kabadiwala, Auditor, Brand, Recycler are used. No "Claim" used as a noun for a Certificate. No violations.
