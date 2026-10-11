# Implementation review: p2-8-redteam-scorecard

Reviewed `src/agent/redteam.py`, `tests/test_redteam.py`, `docs/redteam_scorecard.md`, the `Makefile` target and the new section in `docs/agent_and_policy.md` against the spec and its review. Ran `python -m agent.redteam` twice (the Markdown is byte-identical), `--real` with no key, and the full suite with `MOCK_LLM=1`.

## Findings, ranked

1. **High: one access row was blocked for the wrong reason.** `policy.directory` remembers every store it loaded. After an Arena deleted its temp ledger, the "unknown caller" row (A10) made `authz` refresh from that missing file. The resulting `policy error` deny looked like a block.
   Fixed: each Arena starts with an empty directory and restores the previous one afterwards. `_cedar_denied` no longer counts a `policy error` deny as blocked. A10 now shows `unknown principal`, and tests cover both.

2. **High: two defence texts overstated what the system does.**
   - R1 said it "catches >= 1.2x". The code's threshold is `KK_R1_THRESHOLD` (1.17), and P1's sweep reports 1.5x as the smallest caught with zero false flags. The text now prints the threshold from `radar.rules.r1_threshold()`.
   - K3 said R1 catches a rigged scale upstream. That is wrong: inflated Receipts *raise* verified inflow. The text now gives the real next step, reconciling Receipts sold to a recycler with the recycler's own weighbridge slips.

3. **High: `--real` was silently mocked under `make`.** `make` exports `MOCK_LLM=1` from `.env`. The Arena only skipped setting it, so a "real" run stayed on the scripted model while the headline said "real model".
   Fixed: the Arena sets `MOCK_LLM` explicitly to `0` or `1`. A test covers it.

4. **Medium: the sample world took 18 s per access row** (about 3.5 minutes per run), because of 1,168 single-row transactions.
   Fixed: a small purpose-built world (two kabadiwalas, two brands, Recycler C over-claiming 3x, an auditor). The whole run takes about 11 s, and the Cedar rules exercised are the same.

5. **Medium: model-error count missed S4.** The duplicate-photo row makes two requests and did not count model errors.
   Fixed. With no key, `--real` reports 16 of 16 end-to-end rows as finished by code, rather than claiming a Gemini run.

6. **Low: the "Claim" vocabulary.** `tests/test_agent_hardening.py` bans "Claim" in agent prose; K2's wording used it.
   Fixed ("Pretend to be the auditor").

7. **Low: the docs state the attack count (47).**
   Fixed: a test asserts the number in `docs/agent_and_policy.md` matches `ATTACKS`, so it cannot drift.

## Checked, no change needed
- **Boundary:** no file of the system under attack changed. `agent.agent.build_model` is swapped only inside `compromised()`, which restores it in `finally` (tested, including when the attack raises). The directory internals touched are in P2's own `src/policy/directory.py`.
- **Facts, not text:** every row decides from HTTP status, ledger rows, `verify()` or Flags. M6 proves a lying final message does not change the API result.
- **Determinism:** no Receipt IDs, hashes, times or temp paths in the Markdown (tested).
- **Offline:** `fixture:` payloads always use the stub, including in `--real` (`src/perception/photo.py`, `voice.py`). Tests never use `--real`.
- **Honesty:** 3 controls pass and 3 known limits get through, each with what would catch it. An attack that crashes is a failure, never a pass (tested).
- **Makefile:** one new target with its own `.PHONY` line; no existing line changed.
