# Spec review: p2-2-flag-decisions

Reviewed `docs/specs/p2-2-flag-decisions.md` against CLAUDE.md, CONTEXT.md, `src/common/models.py`, `src/api/app.py` (`principal`, `require`, `Denied`), `src/ledger/store.py` (flags table, `replace_flags`, `decide_flag`), `src/policy/` and the brief. No code was run.

## High

1. **Forbidden-word test contradicts the glossary.** The spec bans "Claim" but the required term "Over-claim ratio" contains it, so a naive test fails on every R1 text. **Applied:** the ban applies to "Claim" as a word for a Certificate; "Over-claim ratio" is stripped before the whole-word check. "fraud", "fake" and "mock" added to the ban (CONTEXT.md avoids "fake"/"mock" for Synthetic; the spec already says "does not match").
2. **Hindi text was untestable.** Only terms were listed, no templates, so "cites the numbers" had no fixed form. **Applied:** explicit Hindi templates for R1, R2, R3 and a shared inspection sentence in both languages.
3. **"Never invent numbers" had holes.** Invalid types (string, bool, NaN, negative), a bad month, an unknown material, `ratio` absent versus `None`, or non-dict `facts` were unspecified, so `explain` could print nonsense or raise. **Applied:** a validity definition, the generic fallback for any invalid fact, `ratio` printed as given (never recomputed), and a parametrised test.
4. **Double-decision race is real in the existing store.** `store.decide_flag` updates unconditionally, so two concurrent requests both pass the pure `open` check and the later one overwrites an Auditor's decision. **Applied (as a P3 note, not a dependency):** make the UPDATE conditional on `status = 'open'`.

## Medium

5. **`model_copy` is shallow:** `facts` would be shared with the input, which breaks "input never mutated". **Applied:** `deep=True` plus `test_facts_not_shared_with_input`.
6. **`test_explain_is_offline` was unreliable:** checking `sys.modules` for `strands` fails whenever another test imported it. **Applied:** parse the two modules with `ast` and check their imports.
7. **`test_numbers_only_from_facts` was under-defined** (digit runs of `12.50` vs `12`, `2026-09`, ids). **Applied:** each digit run must come from a formatted fact value, a printed id, `0.85`, or the "and N more" count; both languages.
8. **Persistence gaps hidden in the P3 notes.** `facts` is not stored, so the explanation must be generated at radar time; the stored `decided_ts` is the store's own clock; `flag_id` must be deterministic or `replace_flags` loses decisions. **Applied:** stated in the notes, plus `test_decision_persists_via_store` to prove the status and actor id round-trip through the real store.
9. **Info leak path:** R2/R3 `facts` and explanations name Kabadiwalas. **Applied:** note that Flags are served to the Auditor only; the Brand view stays aggregate (CONTEXT/Cedar rule).
10. **Duplicate Cedar check.** `app.require()` already raises `Denied` with the same 403 body. **Applied:** the note tells P3 both routes yield identical output; `FlagDenied` is kept because the brief requires a typed error carrying the Decision.

## Low

11. "phash distance" is jargon in auditor-facing text. **Applied:** "perceptual-hash distance" (Hindi "फ़ोटो-हैश दूरी").
12. Console must render explanation text as text, not HTML. **Applied:** one line in `explain` rules (note for P4).
13. Warning log must not leak fact values. **Applied:** log rule and flag_id only.
14. Import style: the repo uses top-level imports with `pythonpath = ["src"]`. **Applied:** noted for P3 and implied for the new modules.

## Rejected

- **Move the Cedar check before the `decision` validation.** The invalid-decision-first order leaks only the two-word vocabulary, which is public in the API. Kept as specified (and tested).
- **Drop `decision_note`, the 500-char cap or `max_hamming`.** They are small, the brief asks for the note, and R2 needs a number to cite. Kept.
- **Persist `facts` or add a note column in `src/ledger`.** Out of scope (teammate module); recorded as a P3 note.
- **Make `decide_flag` atomic itself.** It has no store by design; the conditional UPDATE belongs in P3's store call.
