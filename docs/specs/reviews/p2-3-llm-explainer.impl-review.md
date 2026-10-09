## Fix round

- Failure: `tests/test_radar_explain.py::test_explain_is_offline` (p2-2) walked every import in `src/radar/explain.py`, including the lazy `strands` imports inside `_default_completer`, which spec p2-3 requires.
- Cause: the older test contradicted the newer spec. The code is right (lazy provider import, nothing at module level, no network under `MOCK_LLM=1`).
- Change: the test now checks only module-level imports of `explain.py` for banned modules (lazy imports inside functions are allowed). `decisions.py` is still checked over all imports. Intent kept: importing the module never loads network or model code.
- Verification: not rerun. Shell access was denied in this session after the edit, so `MOCK_LLM=1 python -m pytest -q` still needs to be run.
