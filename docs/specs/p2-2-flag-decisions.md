# Spec p2-2-flag-decisions: Auditor flag decisions and template explanations

## Goal
- **Video beat 2, Fraud caught:** the radar flags Recycler C (R1), the Auditor reads a plain explanation and clicks *Request inspection*; the Flag then shows who decided and when.
- **Design rule 1:** code decides (rules), the human approves (`decide_flag`), the LLM explains. This spec delivers the deterministic *template* explanation; the later LLM explainer falls back to it.
- **Design rule 3:** synthetic subjects are labelled as synthetic in the text.
- Serves the "Auditor decision logic" and "template-text explanation" row of P2 Tier 0 (`research/FINAL_WORK_DIVISION.md`).

## Scope
- `src/radar/__init__.py` (new, empty; `src/radar/rules.py` is P3's and is not touched).
- `src/radar/decisions.py` (new): `decide_flag` and typed errors.
- `src/radar/explain.py` (new, P2-owned): `explain(flag)`, `with_explanation(flag)`.
- `src/common/models.py`: two optional, backward-compatible fields on `Flag` (`facts`, `decision_note`).
- `tests/test_flag_decisions.py`, `tests/test_radar_explain.py` (new).

## Out of scope
- HTTP routes (`/flags/{id}/decision`, `/radar/run`), persistence changes, the LLM explainer, radar rule logic, the console.
- No change to `src/api`, `src/ledger`, `bot/`, `console/`, perception, `src/policy`.

## Dependencies on teammates
None blocking.
- `decide_flag` is a pure function on a `Flag` plus a Cedar call. It needs no store, API or rules. Tests build `Flag` objects by hand.
- Facts are an explicit contract (below). P3's rules fill `Flag.facts`; until then tests use hand-written facts.
- Cedar: `policy.authz.is_allowed` already permits `approve_flag` only for the Auditor (spec p2-1-cedar).
- Non-blocking notes for P3 (not required here; nothing in this feature depends on them):
  - Import style is the repo's top-level one (`from common.models import Flag`, `from policy import authz`), with `pythonpath = ["src"]`; no `src.` prefix.
  - Call `with_explanation(flag)` on each rule's Flag before `store.replace_flags`. The store persists `explanation_en/hi` but **not** `facts`, so the explanation must be generated at radar time, while `facts` are in hand.
  - In the decision route: load the Flag with `store.get_flag` (404 if missing), call `decide_flag`, then persist with `store.decide_flag(flag_id, new.status, new.decided_by)`. The store stamps its own time (the stored `decided_ts` can differ slightly from the returned Flag's) and has no note column, so the note lives only in the returned Flag until P3 adds a column. Return the stored Flag.
  - `app.require()` already runs the same Cedar check and raises `Denied`. P3 may call `require(who, "approve_flag", {"type": "Flag", "id": flag_id})` first, or catch `FlagDenied` and `raise Denied(exc.decision, "approve_flag")`. Both give the same 403 body.
  - Map errors to HTTP: `FlagDenied` -> 403 with `exc.decision.to_denial("approve_flag")`; `InvalidDecision` -> 422; `FlagAlreadyDecided` -> 409.
  - Race: `decide_flag` is pure, so two concurrent requests can both read `open`, and `store.decide_flag` updates unconditionally, so the later one overwrites. P3 should make the update conditional (`WHERE flag_id = ? AND status = 'open'`, 409 on zero rows). Not blocking for the single-user demo.
  - `flag_id` must be deterministic across radar runs, because `replace_flags` carries decisions over by `flag_id`.
  - R2 and R3 `facts` name Kabadiwalas. Serve Flags and their explanations only to the Auditor; the Brand's provenance view stays aggregate.

## Interfaces

### `src/common/models.py` (additive only)
```python
class Flag(BaseModel):
    ...existing fields unchanged...
    facts: dict = Field(default_factory=dict)       # numbers an explanation may cite; keys per rule below
    decision_note: Optional[str] = None             # Auditor's free text, set by decide_flag
```
Existing `Flag(**row)` construction in the store keeps working (both fields default).

### Facts contract (the only numbers explanations may use)
Keys are required for their rule unless marked optional. Values are JSON-safe.
| Rule | Key | Type | Meaning |
|---|---|---|---|
| R1_mass_balance | `recycler_id` | str | Recycler (also `flag.subject_id`) |
| | `recycler_name` | str, optional | display name |
| | `month` | str `"YYYY-MM"` | calendar month (India time) |
| | `material` | str | a `Material` value |
| | `certificate_tonnes` | float | summed Certificate tonnes for recycler, material, month |
| | `verified_inflow_tonnes` | float | Verified inflow |
| | `ratio` | float or null | Over-claim ratio = certificate_tonnes / (verified_inflow_tonnes x 0.85); equals `flag.score`; null if inflow is 0 |
| | `synthetic` | bool, optional (default false) | subject is seeded demo data |
| R2_duplicate_photo | `receipt_ids` | list[str] | Receipts sharing a near-identical photo (also `flag.evidence_ids`) |
| | `collector_ids` | list[str] | Kabadiwalas those Receipts belong to |
| | `max_hamming` | int | largest pairwise phash distance in the cluster |
| | `synthetic` | bool, optional | |
| R3_broken_chain | `collector_id` | str | the Chain's Kabadiwala (also `flag.subject_id`) |
| | `broken_seq` | int | first seq where verification fails |
| | `receipt_id` | str, optional | Receipt at `broken_seq` (also in `evidence_ids`) |
| | `synthetic` | bool, optional | |

### `src/radar/decisions.py`
```python
class FlagDecisionError(Exception): ...
class FlagDenied(FlagDecisionError):          # Cedar said no
    decision: policy.authz.Decision           # .to_denial("approve_flag") is the 403 body
class InvalidDecision(FlagDecisionError): ... # decision not in {"inspect", "dismiss"}
class FlagAlreadyDecided(FlagDecisionError):  # flag.status != "open"
    status: str

def decide_flag(flag: Flag, principal: str, decision: str, note: str | None = None,
                now: datetime | None = None) -> Flag
```
- `principal` is a Cedar UID string (`Actor::"auditor-1"`), as `app.principal()` yields.
- Returns a **new** Flag built with `flag.model_copy(update=..., deep=True)` (so `facts` is not shared with the input); the input is never mutated.

### `src/radar/explain.py`
```python
def explain(flag: Flag) -> tuple[str, str]          # (english, hindi)
def with_explanation(flag: Flag) -> Flag            # copy with explanation_en / explanation_hi filled
```

## Behaviour and rules

### decide_flag
Checks in this order, first failure wins:
1. `decision` not in `{"inspect", "dismiss"}` -> `InvalidDecision` (a malformed request is not a policy question).
2. Cedar: `is_allowed(principal, "approve_flag", {"type": "Flag", "id": flag.flag_id})`. Denied -> `FlagDenied(decision)`. Cedar runs **before** the status check so a non-Auditor learns nothing about a Flag's state.
3. `flag.status != "open"` -> `FlagAlreadyDecided(status)`. No re-deciding, even with the same decision.
4. Success: `inspect` -> `status="inspection_requested"`; `dismiss` -> `"dismissed"`. Set `decided_by` to the actor id (the `<id>` inside `Actor::"<id>"`), `decided_ts = now or datetime.now(timezone.utc)` (tz-aware UTC; a naive `now` is treated as UTC), `decision_note` = stripped note, `None` if blank, truncated to 500 chars.
- Transition table: `open -> inspection_requested | dismissed`; no other transition exists. `rule`, `score`, `evidence_ids`, `facts` and explanations carry over unchanged.
- Cedar is the only authorization; no role-string comparison in code.

### explain
- Pure, deterministic, offline. Reads only `flag.rule`, `flag.subject_id`, `flag.evidence_ids`, `flag.facts`. Formats: tonnes `:.2f`, ratio `:.1f` followed by `x` (Hindi: ` गुना`, e.g. `38.0 गुना`), seq as an integer. Digits are always ASCII.
- A fact is **valid** if it has the stated type: numbers are finite `int`/`float` (not `bool`, not NaN/inf, not negative); `month` matches `^\d{4}-(0[1-9]|1[0-2])$`; `material` is in `common.models.MATERIALS`; lists are lists of non-empty `str`; `broken_seq` is an `int >= 0`. A missing or invalid required fact triggers the generic fallback below. The `ratio` key must be **present**: absent = missing; present `None` means "undefined" and is valid only when `verified_inflow_tonnes == 0`.
- `explain` prints `facts.ratio` as given; it never recomputes it.
- Text is plain Unicode; the console must render it as text, not HTML (note for P4). Fact strings (`recycler_name`, ids) are inserted verbatim, never interpreted.
- English vocabulary (CONTEXT.md): "Certificate", "Verified inflow", "Over-claim ratio", "Chain", "Receipt", "Kabadiwala", "Recycler", "Auditor". Never "Claim" (as a word for a Certificate), "Collector", "Alert", "Supply", "Fraud score", "fraud", "fake", "mock". The glossary term "Over-claim ratio" itself is allowed.
- Hindi terms are fixed in one module-level dict so tests can check them: Certificate `प्रमाणपत्र`, Verified inflow `सत्यापित आवक`, Over-claim ratio `ओवर-क्लेम अनुपात`, Chain `चेन`, Receipt `रसीद`, Kabadiwala `कबाड़ीवाला`, Recycler `रीसाइक्लर`.
- Each text states: which rule fired, the numbers, the evidence ids (`flag.evidence_ids`, first 5, then "and N more" / "और N"), and that an inspection can be requested. Wording is "does not match", never "is fraudulent".
- R1 English: `"<Recycler> issued Certificates for <T> tonnes of <material> in <month>, but its Verified inflow is <V> tonnes. Over-claim ratio: <R>x (Certificate tonnes divided by Verified inflow x 0.85). Evidence: <ids>."`
- R2: `"<N> Receipts from <K> Kabadiwalas use near-identical photos (largest perceptual-hash distance <d>). Evidence: <ids>."`
- R3: `"The Chain of Kabadiwala <id> breaks at seq <n>: that Receipt no longer matches its hash, so none of this Kabadiwala's Receipts count towards Verified inflow. Evidence: <ids>."`
- Hindi templates (same facts, same order, terms from the fixed dict):
  - R1: `"<Recycler> ने <month> में <material> के <T> टन के प्रमाणपत्र जारी किए, लेकिन उसकी सत्यापित आवक <V> टन है। ओवर-क्लेम अनुपात: <R> गुना (प्रमाणपत्र टन ÷ (सत्यापित आवक × 0.85))। प्रमाण: <ids>।"`
  - R2: `"<K> कबाड़ीवाला की <N> रसीदों में लगभग एक जैसी फ़ोटो है (सबसे बड़ी फ़ोटो-हैश दूरी <d>)। प्रमाण: <ids>।"`
  - R3: `"कबाड़ीवाला <id> की चेन seq <n> पर टूटती है: वह रसीद अपने हैश से मेल नहीं खाती, इसलिए इस कबाड़ीवाला की कोई भी रसीद सत्यापित आवक में नहीं गिनी जाती। प्रमाण: <ids>।"`
  - Each text ends with the inspection sentence, before the synthetic label: EN `" An Auditor can request an inspection."`, HI `" ऑडिटर निरीक्षण का अनुरोध कर सकता है।"`.
- If `facts.synthetic` is true, append ` (Synthetic demo data.)` / ` (सिंथेटिक डेमो डेटा।)`.
- Missing required fact: never invent or default a number. Emit a generic sentence with no figures (`"Rule R1_mass_balance flagged <subject_id>. Evidence: <ids>."` plus Hindi) and log a warning (rule and flag_id only, never fact values). The synthetic label is still appended if `facts.synthetic is True`. `explain` never raises on bad facts; `facts` that is not a dict is treated as empty.
- `ratio is None` (zero inflow): the R1 text says Verified inflow is 0 tonnes so the Over-claim ratio is undefined; no ratio figure.
- `with_explanation` never overwrites a non-empty `explanation_en/hi`, so a later LLM text survives.

## Edge cases
- Principal is a Kabadiwala, Brand, Recycler, the Agent, unknown or malformed: `FlagDenied`; Flag untouched.
- `decision` of `"INSPECT"`, `""`, `None`, `"approve"`: `InvalidDecision`.
- Second decision on a decided Flag (same or opposite): `FlagAlreadyDecided`.
- `note` whitespace-only -> `None`; over 500 chars truncated; the note is data, never interpreted.
- `evidence_ids` empty: `Evidence: none recorded` / `प्रमाण: कोई दर्ज नहीं`.
- Unknown extra keys in `facts` are ignored; missing `recycler_name` falls back to `subject_id`.
- Text is plain, no markup, so it is safe to show in the console.

## Test plan
`tests/test_flag_decisions.py` (uses the existing `actor_directory` autouse fixture; Auditor is `Actor::"auditor-1"`):
- `test_inspect_sets_inspection_requested`, `test_dismiss_sets_dismissed`
- `test_records_decided_by_ts_and_note`
- `test_naive_now_treated_as_utc`, `test_default_now_is_utc_aware`
- `test_input_flag_not_mutated`, `test_other_fields_preserved`
- `test_blank_note_becomes_none`, `test_long_note_truncated`
- `test_double_decision_same_raises_already_decided`, `test_double_decision_opposite_raises`
- `test_invalid_decision_raises` (parametrised: `"approve"`, `""`, `None`, `"INSPECT"`)
- `test_brand_denied_with_cedar_body` (`exc.decision.to_denial("approve_flag")["denied_by"] == "cedar"`)
- `test_kabadiwala_recycler_agent_unknown_denied` (parametrised)
- `test_denied_before_status_check`, `test_invalid_decision_checked_before_cedar`
- `test_flag_defaults_backward_compatible` (old-style `Flag(...)`: `facts == {}`, `decision_note is None`)
- `test_facts_not_shared_with_input` (mutating the result's `facts` leaves the input's untouched)
- `test_decision_persists_via_store` (temp `Store`: `replace_flags`, then `store.decide_flag(new.flag_id, new.status, new.decided_by)` stores the same status and actor id)

`tests/test_radar_explain.py`:
- `test_r1_english_contains_numbers_ids_vocab` (38x case: certificate tonnes, inflow tonnes, month, material, evidence id)
- `test_r1_hindi_contains_numbers_ids_terms`
- `test_r2_english_and_hindi`, `test_r3_english_and_hindi` (broken seq and receipt id present)
- `test_numbers_only_from_facts` (split text into digit runs; each must come from a formatted fact value, a printed id, the fixed `0.85`, or the "and N more" count; English and Hindi)
- `test_no_forbidden_words` (English output of all rules and the generic fallback; whole-word, case-insensitive; "Over-claim ratio" removed first)
- `test_invalid_fact_types_give_generic_text` (parametrised: string tonnes, bool, NaN, negative, bad month, unknown material, `facts=None`, ratio key absent, ratio `None` with non-zero inflow)
- `test_hindi_templates_use_fixed_terms`, `test_explanation_mentions_inspection_option`
- `test_synthetic_label_present_when_fact_true`, `test_synthetic_label_absent_when_false`
- `test_missing_fact_gives_generic_text_without_numbers` (per rule, no exception)
- `test_zero_inflow_ratio_none_says_undefined`
- `test_evidence_truncation_over_five`, `test_empty_evidence_text`
- `test_deterministic`
- `test_with_explanation_fills_and_keeps_existing`
- `test_explain_is_offline` (runs under `MOCK_LLM=1`; parse `explain.py` and `decisions.py` with `ast` and assert no import of `strands`, `requests`, `httpx`, `urllib` or `socket`; do not inspect `sys.modules`, since other tests import `strands`)

## Acceptance criteria
- `MOCK_LLM=1 python -m pytest -q` (or `make test`) passes with all tests above and the existing suite, offline.
- Every transition in the table is tested; every other path raises a typed error and leaves the Flag unchanged.
- A Brand calling `decide_flag` gets a `FlagDenied` whose `decision.to_denial("approve_flag")` is `{"denied_by": "cedar", "action": "approve_flag", "reason": ...}`.
- Each rule has English and Hindi text citing the facts' numbers and evidence ids, using CONTEXT.md terms and no invented figures.
- `Flag` gains only the two optional fields; nothing under `src/api`, `src/ledger`, `bot/`, `console/` changes.
- No secrets, absolute paths or personal names in the new files.

## Deviations
None from the behaviour above. Implementation choices the spec left open:
- The generic fallback text also gets the inspection sentence (and the synthetic label when set), like the rule texts.
- R2's "K Kabadiwalas" counts distinct ids in `collector_ids`; "N Receipts" is `len(receipt_ids)`.
- `max_hamming` and `broken_seq` must be `int` (not float) to be valid.
