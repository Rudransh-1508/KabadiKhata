# Spec p2-6-radar-explanations-live: the live radar uses P2's explainer

## Goal
- **Video beat 2, Fraud caught:** the Auditor's explanation of the Recycler C Flag comes from P2's explainer, built from facts P2 derives, so the console caption "code decides, the LLM only explains" is true.
- **Design rule 1** (CLAUDE.md): the verdict is the rule's. This feature only chooses the words, and never touches `rule`, `subject_id`, `score`, `evidence_ids` or `status`.
- **Honesty about Chain breaks:** when a Kabadiwala's Chain breaks, that Kabadiwala's later Receipts stop counting as Verified inflow, so an honest Recycler that bought from them can be flagged by R1. The explanation says so and points the Auditor to the R3 Flag first.

## Problem (verified)
`rules.run()` calls `_explain` -> `with_llm_explanation(flag)`. Every rule Flag already carries `explanation_en` and `explanation_hi` and an empty `facts`, so `with_llm_explanation` returns at its first line (text already set) and neither the templates nor the LLM ever run.

## Scope
- `src/radar/facts.py` (new, P2): `derive_facts(flag, store) -> dict`, read-only.
- `src/radar/explain.py`: `with_llm_explanation(..., store=None)` chooses the text; R1 template gets a broken-Chain note; optional facts keys; LLM prompt and validator know them.
- `src/common/models.py`: one additive field on `Flag`: `explanation_source: Optional[Literal["rule","template","llm"]] = None`.
- `src/radar/rules.py`: exactly one line, the body of `_explain`: `return with_llm_explanation(flag, store=store)`. Docstring stays accurate ("fills text and facts; never the verdict").
- `docs/agent_and_policy.md` section 4, `src/agent/README.md` (one line if it mentions radar explanations).
- New tests: `tests/test_radar_facts.py`, `tests/test_radar_live_explain.py`.
- **One called-out edit to an existing P2-authored test** (see "Conflict with an existing test"): `tests/test_radar_explain.py::test_radar_run_explains_flags`.

## Conflict with an existing test (must be resolved, not ignored)
`tests/test_radar_explain.py::test_radar_run_explains_flags` (P2's own test, from PR #8) ends by asserting that `rules.run()` Flags have the same `facts` as the raw rule Flags, i.e. `{}`. Attaching derived facts (brief item 3) makes that assertion false, so "all existing tests pass unchanged" cannot hold for that one line. Decision: change only that final assertion so it compares `(rule, subject_id, score, evidence_ids, status)` between `rules.run()` and the raw rule Flags (the verdict, which is what the test is really protecting) and no longer compares `facts`. The change is called out in the hand-off; no other existing test is touched. Every other existing test (including P3's wording assertions in `tests/test_rules.py`, which hold because MOCK_LLM keeps the rule text when no Chain is broken) must pass unchanged; verify by running the full suite.

## Out of scope
- Any other code in `rules.py`; `src/ledger`, `src/api`, `bot/`, `console/`, `src/perception`, `src/synth`, `eval/`; any existing test file.
- Persisting `facts` or `explanation_source`: `Store.replace_flags` writes only the two text columns, so after `POST /radar/run` the stored Flag has the text but not the facts or source. Noted for P3 (non-blocking; the text is what the console renders).
- Changing R1/R2/R3 thresholds, scoring or grouping. Making the radar async.

## Dependencies on teammates
None blocking. Facts are derived only from P3's public, already-merged helpers: `rules.chain_status`, `rules.verified_receipts`, `rules.verified_inflow_t`, `rules.certified_t`, `rules.over_claim_ratio`, `rules.hamming`, `rules.YIELD`, `chain.month_ist`, `chain.verify`, and `Store.list_certificates`, `.receipts_for`, `.get_receipt`, `.get_actor`, `.collector_ids`. Nothing is added to P3 or P4 code. If a helper's signature changes, derivation raises, is caught, and the Flag keeps its rule text (see Edge cases), so the radar never breaks. `facts.py` imports `radar.rules` lazily inside the function (rules imports explain lazily too) to avoid an import cycle.

## Interfaces

### `src/radar/facts.py`
```python
def derive_facts(flag: Flag, store: Store) -> dict:
    """JSON-safe facts per the contract at the top of explain.py; {} when the Flag or store does not support them."""
```
Pure function of `(flag, store)`; no writes, no network, no clock. It recomputes with the rule's own helpers, so it cannot drift from the rule.

**R1_mass_balance** (`flag.evidence_ids` are Certificate ids):
1. Load Certificates by `store.list_certificates()` whose id is in `evidence_ids`. Require that every evidence id is found, that there is at least one, that they share one `(recycler_id, material, month)` key, and that `flag.subject_id == recycler_id`; otherwise `{}`.
2. `status = rules.chain_status(store)`; `verified = rules.verified_receipts(store, status)`; `inflow = rules.verified_inflow_t(verified).get(key, 0.0)`; `certified = rules.certified_t(store.list_certificates(recycler_id=...)).get(key, 0.0)`.
3. `certificate_tonnes = certified`, `verified_inflow_tonnes = inflow`, `ratio = rules.over_claim_ratio(certified, inflow)`, with `inf` stored as `None` (contract: None only when inflow is 0).
   **Consistency guard (the explanation must describe the verdict the rule gave):** if `ratio` is finite and `flag.score != approx(min(ratio, 999.0))`, or `ratio` is `None` and `flag.score != 999.0`, return `{}` (the store changed between the rule run and derivation, or the helpers drifted). The Flag then keeps its rule text.
4. Excluded: for each `cid, res` in `status` with `res.broken_at_seq is not None`, sum `weight_kg / 1000` of `store.receipts_for(cid)` with `seq >= broken_at_seq`, `recycler_id == key[0]`, `material == key[1]`, `chain.month_ist(ts) == key[2]`. Keys `excluded_tonnes` (float, rounded to 6 places) and `excluded_collector_ids` (sorted list of collectors contributing > 0). Both are always written for R1 (0.0 and `[]` when none). These are tonnes **as currently stored**: the tamper tool can edit `weight_kg`, `material` and `recycler_id` of a Receipt (`ledger.world.TAMPERABLE`), so a Receipt whose own fields were edited may be attributed to a different key than the one it was originally sold under. The note says "recorded" (not "sold") and the Auditor is pointed to R3 for exactly this reason; the limitation is stated in the doc.
5. `recycler_name` from `store.get_actor(recycler_id).name` when it exists (omitted otherwise). `synthetic: True` only when the Receipts behind this key (verified inflow plus excluded) exist and all have `synthetic` true; otherwise the key is omitted (Certificates and Actors carry no synthetic marker, so a key with no Receipts cannot be labelled by facts; the rule's own text is then kept).

**R2_duplicate_photo**: Receipts via `store.get_receipt` for each evidence id (all must exist, at least 2). Also require `flag.subject_id == ",".join(collector_ids)`. `receipt_ids` = sorted evidence ids; `collector_ids` = sorted distinct collectors; `max_hamming` = max pairwise `rules.hamming(phash, phash)` (every Receipt must have a phash); `synthetic` only when all are synthetic.

**R3_broken_chain**: `collector_id = flag.subject_id`; `broken_seq = chain.verify(store.receipts_for(collector_id)).broken_at_seq` (must be not None, else `{}`); `receipt_id = evidence_ids[0]` when present; `synthetic` only when all that Kabadiwala's Receipts are synthetic.

Floats are plain Python floats; no NaN or inf ever appears in the dict.

### `src/radar/explain.py`
- Facts contract docstring gains OPTIONAL R1 keys: `excluded_tonnes` float >= 0 (tonnes sold to this Recycler, material and month on Receipts left out because their Chain is broken), `excluded_collector_ids` list[str].
- `_FACT_KEYS["R1_mass_balance"]` gains both keys, so the LLM sees them and the number validator allows `excluded_tonnes`.
- `_r1` appends, only when `excluded_tonnes > 0` and `excluded_collector_ids` is a non-empty list of strings (else no note, so existing template output is byte-for-byte unchanged):
  - EN: ` Note: {x:.2f} tonnes of this Recycler's inflow came from Receipts of Kabadiwala(s) {ids} whose Chain is broken, so they do not count as Verified inflow. Check the R3 Flag for them first.`
  - HI: ` ध्यान दें: इस रीसाइक्लर की {x:.2f} टन आवक कबाड़ीवाला {ids} की उन रसीदों से आई जिनकी चेन टूटी है, इसलिए वह सत्यापित आवक में नहीं गिनी गई। पहले उनका R3 फ़्लैग देखें।`
  - `ids` uses the same 5-id limit style as `_evidence`. The note comes before the inspection and synthetic suffixes.
- `SYSTEM_PROMPT` gains one sentence (when `excluded_tonnes` is above 0, say those Receipts were left out because their Chain is broken and to check the R3 Flag first); `PROMPT_VERSION` becomes `"v2"` (invalidates cached text).
- `_validate` number check: the note necessarily says "R3", whose digit would otherwise fail `number not in facts`. When `excluded_tonnes > 0`, remove the literal token `R3` from the text (alongside the known-string stripping) before the number scan. Nothing else is allowed through.
- `_validate`: when facts have `excluded_tonnes > 0`, reject with reason `"broken-chain note missing"` unless the English text contains "chain" (case-insensitive) and the Hindi text contains "चेन", and each contains at least one id from `excluded_collector_ids`.
- Signature: `with_llm_explanation(flag, *, complete=None, cache_dir=None, store=None) -> Flag`. `store` is typed `Any` / under `TYPE_CHECKING`; `explain.py` stays free of ledger imports and imports `radar.facts` lazily.
- The stale module docstring line ("The LLM explainer, when added, ...") is updated to describe the explainer as live.

### Choosing the text (`store` given)
```
facts = flag.facts or derive_facts(flag, store)      # any exception -> {}
f2    = flag with facts
ex    = explain_flag(f2, complete=complete, cache_dir=cache_dir)
if ex.source == "llm":                          -> ex text,           source "llm"
elif R1 facts show excluded_tonnes > 0:         -> ex template text,  source "template"
elif rule text (both en and hi) is set:         -> rule text,         source "rule"
else:                                           -> ex template text,  source "template"
```
Result is `flag.model_copy(update={explanation_en, explanation_hi, facts, explanation_source}, deep=True)`. Nothing else is updated. Without `store` (legacy callers, existing tests) behaviour is unchanged: existing text is kept (source `"rule"`), empty text is filled from `explain_flag` (its source). `explain_flag` and `explain` signatures do not change.

When is the LLM text shown? A key is set (`GEMINI_API_KEY` / `OPENAI_API_KEY` per `LLM_PROVIDER`), `MOCK_LLM` is not 1, the call finishes within `LLM_EXPLAIN_TIMEOUT_S`, and validation passes. Any other case falls through the ladder above. Without a key the console shows the rule's own text (or, with a broken Chain, the template).

## Behaviour and rules
1. The verdict fields are copied through untouched; a test compares them before and after.
2. Derived R1 `ratio` equals `flag.score` when finite (`score = min(ratio, 999)`); when `ratio is None` the Flag's score is 999.0.
3. Facts are never invented: any missing Certificate, Receipt or phash, or a failed consistency guard, gives `{}`, and an empty `facts` means `explanation_source = "rule"` (rule text kept; `"template"` only if the rule text itself is empty). A missing Actor only omits `recycler_name`.
4. `MOCK_LLM=1` and no injected `complete`: `explain_flag` returns the template without any network call (existing behaviour). In that mode the rule text is kept except when R1 `excluded_tonnes > 0`. P3's tests assert P3's wording, so they must pass unchanged.
5. A text change never changes `status`; `decide_flag` copies the Flag, so `facts` and `explanation_source` survive a decision (tested).
6. Per-Flag cost: `derive_facts` re-runs `chain_status` (one pass over all Receipts; fine at ~1,000). No cache, because a cache could go stale after a tamper.

## Privacy and policy
- Flags are readable only by the Auditor (Cedar `read_flags`, `auditor-oversight`); no Brand or Agent path exposes them, and this feature adds no route. Explanations now name Kabadiwala ids (excluded collectors); that stays inside the Auditor surface.
- With a key set, `facts` (Recycler name, Kabadiwala ids, tonnes) are sent to the external LLM provider and cached on disk under the cache dir. Ids are pseudonymous and the data is synthetic in the demo; the doc says so. No Receipt PII (voice text, photos, locality) is in the facts.
- The text remains untrusted data for the console (rendered as text). Only the `_FACT_KEYS` allowlist reaches the model.

## Edge cases
- R1 for a Recycler with zero verified inflow: `ratio None`, `verified_inflow_tonnes 0.0`; if everything was excluded, the note applies.
- Certificates for one key spanning several Brands: `certificate_tonnes` is the sum, like the rule; evidence ids list them all.
- Honest Recycler flagged because of a tampered upstream Chain: note names the Kabadiwala(s); the R3 Flag for the same Kabadiwala is in the same run.
- A Chain that breaks at seq 0: every Receipt of that Kabadiwala is excluded.
- Receipts with no `recycler_id` are never counted (matches `verified_inflow_t`).
- `store` closed or raising: `derive_facts` raises, `with_llm_explanation` catches `Exception`, logs the type only, and keeps the rule text.
- Rejected LLM output (extra number, missing evidence id, forbidden word, missing broken-Chain note) -> not "llm"; ladder continues. A cached hit that now fails validation is dropped (existing behaviour).
- LLM latency: an uncached key-set run can take up to `LLM_EXPLAIN_TIMEOUT_S` per Flag inside `POST /radar/run`; the disk cache makes reruns instant. Call out in the doc; warm the cache before the video.
- The unknown-key case (`GEMINI_API_KEY` unset with `MOCK_LLM` off) is caught inside `explain_flag` ("LLM unavailable: KeyError") and never raises.

## Test plan (new files only; no network; build stores like `tests/test_rules.py` does, by copying the pattern, not importing it)
`tests/test_radar_facts.py`
- `test_r1_facts_match_rule_numbers`: certified, inflow, ratio, month, material, recycler_name present.
- `test_r1_ratio_equals_flag_score`: for several over-claim factors, `facts["ratio"] == pytest.approx(flag.score)`.
- `test_r1_no_inflow_gives_ratio_none`.
- `test_r1_excluded_tonnes_and_collectors_after_chain_break`: tamper one Kabadiwala's seq 1; excluded equals tonnes from seq >= 1 only for that Recycler, material, month.
- `test_r1_excluded_zero_when_chains_intact`.
- `test_r2_facts_ids_collectors_max_hamming`.
- `test_r3_facts_collector_and_broken_seq`.
- `test_facts_empty_when_evidence_missing` (unknown Certificate id, unknown Receipt id).
- `test_derive_facts_does_not_write` (store content equal before and after).
- `test_synthetic_only_when_all_receipts_synthetic`.

`tests/test_radar_live_explain.py`
- `test_accepted_llm_gives_source_llm_and_same_verdict`: fake `complete` returns a text that passes `_validate`; `rule/subject_id/score/evidence_ids/status` unchanged.
- `test_rejected_llm_keeps_rule_text`: fake returns an extra number; source `"rule"`, text equals the rule's.
- `test_rejected_llm_with_chain_break_uses_template_with_note`: note contains excluded tonnes, collector ids, "R3", Hindi "R3 फ़्लैग".
- `test_llm_without_broken_chain_note_is_rejected_when_excluded`.
- `test_broken_chain_without_llm_uses_template_note` (MOCK_LLM=1).
- `test_mock_llm_keeps_rule_text_without_chain_break`.
- `test_mock_llm_makes_no_network_call`: patch `socket.socket.connect` and `explain._default_completer` to fail the test if used.
- `test_facts_failure_keeps_rule_text`: store whose `list_certificates` raises.
- `test_rules_run_end_to_end_sets_facts_and_source`: `rules.run(store)` Flags all have non-empty `facts` and a source; `(rule, subject_id, score, evidence_ids, status)` equals that of the raw rule output (`r1_mass_balance` + `r2_duplicate_photos` + `r3_broken_chains`, no explainer).
- `test_r1_facts_empty_when_score_disagrees`: a Flag whose score does not match the recomputed ratio (store changed after the run) yields `{}` and the rule text.
- `test_llm_text_with_r3_token_passes_number_check`: a fake reply that says "R3 Flag" with excluded tonnes is accepted; a reply with any other stray digit is still rejected.
- `test_excluded_uses_stored_values_after_recycler_edit`: documents the limitation (a tampered `recycler_id` moves the Receipt's tonnes to the other key).
- `test_legacy_call_without_store_unchanged`.
- `test_decide_flag_keeps_facts_and_source`.
- `test_template_unchanged_without_excluded_keys`: R1 template output equals today's string for the old facts shape.
- Full suite: `MOCK_LLM=1 python -m pytest -q` (or `make test`) passes with no existing test modified.

## Acceptance criteria
1. `git diff --stat` touches only: `src/radar/explain.py`, `src/radar/facts.py`, `src/common/models.py` (one optional field), one line in `src/radar/rules.py`, the two docs, the two new test files, and the single called-out assertion in `tests/test_radar_explain.py` (`src/radar/decisions.py` only if a test proves it drops fields; expected: untouched).
2. `rules.run()` on the seeded world (`ledger.world`: Recycler C, one tampered Receipt, a duplicate-photo ring) returns R1, R2 and R3 Flags each with non-empty `facts` and `explanation_source` set.
3. R1 derived ratio equals `flag.score` for every finite case tested.
4. Broken-Chain case yields the template with the note (English and Hindi), excluded tonnes and Kabadiwala ids, source `"template"`.
5. A fake accepted completer yields source `"llm"` with verdict fields byte-identical to the rule's.
6. A rejected completer falls back per the ladder; MOCK_LLM=1 makes zero network calls.
7. `docs/agent_and_policy.md` section 4 states the fallback order, when the LLM text appears (key set, validation passed), that without a key the rule's text is shown, and that facts and source are not persisted by the store.
8. All existing tests pass, with the one assertion above as the only change to an existing test; no secrets, absolute paths or attribution text added; Python 3.10 compatible; Hindi text uses CONTEXT.md terms (Certificate, Verified inflow, Kabadiwala, Recycler, Receipt, Chain).
