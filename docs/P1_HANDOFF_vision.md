# P1 handoff: real photo vision (`read_photo`)

**Why this is the priority:** the bot and backend are wired end-to-end, but the
agent cannot actually *see* the photo yet. Today `read_photo` is a deterministic
stub that returns a fixed reading regardless of the image, so the bot accepts a
photo of a watch, a wall, anything. Beat #1 of the pitch — *"the agent reads the
photo and refuses a bad collection"* — only becomes real when this lands.

The team decided (see the "refusal demo" choice): **real vision for the live
shot, with the scripted fixture path kept as the deterministic fallback.** So
your job is the real half; do **not** remove the fixture/stub path.

## The contract (do not change the signature)
`read_photo(photo_b64: str) -> common.models.PhotoRead`

```python
class PhotoRead(BaseModel):
    kg: Optional[float]      # scale reading in kg, or None if the scale is unreadable / absent
    material: Material       # one of common.models.MATERIALS (PET, HDPE, LDPE_film,
                             #   mixed_plastic, cardboard, paper, metal, ewaste, unknown)
    confidence: float        # 0.0–1.0
```

Rules the downstream logic already depends on (`src/agent/consistency.py`):
- **Not a scale / number unreadable → return `kg=None`** (consistency asks for a
  clearer photo). Do the same, or `confidence < 0.60`, when unsure.
- **Can't identify the material → `material="unknown"`** (consistency treats it as
  a warning, not a hard fail).
- `material` must be exactly one of the `Material` literals — never a free string.
- Keep a single call under ~25 s (CLAUDE.md #2).

If you return these honestly, the existing consistency rules handle the rest:
a watch → `kg=None` → refusal; "12 kg on the scale but tapped 20" → `kg_mismatch`
→ refusal; wrong material group → `material_mismatch` → refusal.

## Where to plug in
`read_photo` is selected by the `Perception` dataclass in `src/agent/tools.py`:

```python
@dataclass
class Perception:
    read_photo: Callable[[str], PhotoRead] = stub_tools.read_photo   # <- this
    transcribe: ... = stub_tools.transcribe
    phash_check: ... = stub_tools.phash_check
```

Two things to do:
1. **Implement** the real function (suggest `src/perception/photo.py`), e.g. a
   Gemini vision call on the decoded image bytes, returning `PhotoRead`.
2. **Wire it in** so it's used when we're not in mock mode. `MOCK_LLM` currently
   swaps only the agent's *model* (`agent.build_model`), **not** these tools — so
   the default `Perception` uses the stub even with `MOCK_LLM=0`. Add a switch:
   make `Perception`'s default pick the real `read_photo` when
   `config.mock_llm()` is False (and keep the stub when True). Add a
   `config.vision_provider()` if you want it configurable.

## How to run it the way the bot will
- Put `GEMINI_API_KEY=...` in `.env` (gitignored).
- Run the API with real vision: `MOCK_LLM=0 make api` (or `uv run uvicorn api.app:app --port 3000`).
- Run the bot against it: `KK_USE_MOCK=0 uv run python -m bot.telegram_bot`.
- The bot's `/demo` keeps working **without** a key: it sends a fixture photo that
  the stub decodes (the `MOCK_LLM=1` fallback), so a rate-limit or no-key situation
  on demo day still shows the refusal.

## The MOCK_LLM limitation you're removing
In `MOCK_LLM=1` the stub returns a fixed **12 kg PET**, so a legit collection of
any other weight is refused. That's fine for scripted demos (tap ~12 kg) but is
why real vision is needed for genuine use.

## Eval (CLAUDE.md #6 — needed for the README/video)
`eval/photo_eval.py`: split our own photos 20 tune / 10 held-out
(`data/real_own/split.csv`), tune prompts on the tune set only, and report **kg
accuracy within ±5%** and **material accuracy on the held-out set only**, stating
n. That number goes in the README and the video.

## What's already done for you
- The bot resizes photos to ≤1024 px and base64-encodes them (CLAUDE.md #3).
- `POST /collections` decodes, size-checks (≤5 MB), stores the photo, and calls
  the agent. You only implement `read_photo`.
- `phash_check` (duplicate detection) and `consistency` are done; don't touch.
