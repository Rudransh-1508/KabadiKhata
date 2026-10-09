"""Look-alike photos: is this photo of the same load as an earlier one, maybe from another angle?

A perceptual hash (R2) catches the same photo resent or lightly edited, but a new photo of the same
sack from another angle hashes completely differently. Here each photo becomes a DINOv2-small image
embedding (a model trained on visual similarity), and two photos are compared by cosine similarity,
which holds up across viewpoints.

This only measures and reports similarity. Whether a look-alike pair becomes an Auditor flag is a
team decision (it would need a radar rule and a new Flag.rule value); it must never auto-refuse a
Collection, because photos from one shop all look alike.

Optional: needs `uv sync --extra dedupe` (onnxruntime, numpy). The model (88 MB, Apache-2.0,
facebook/dinov2-small exported by onnx-community) downloads once into the cache, pinned to a
revision and checked against its SHA-256.
"""
from __future__ import annotations

import hashlib
import io
import os
import urllib.request
from functools import lru_cache
from typing import Iterable, Optional

from common import config

MODEL_REVISION = "8b1f705a3a7f6f062f6bdd21986c1583d3ef105d"
MODEL_URL = f"https://huggingface.co/onnx-community/dinov2-small/resolve/{MODEL_REVISION}/onnx/model.onnx"
MODEL_SHA256 = "f22797eabf810a75e41de68d378541ebea372122b25c4ce3ef25ff618250c20a"
SIZE, CROP = 256, 224                       # resize the short side to 256, centre-crop 224 (DINOv2 preprocessing)
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
# Where the pan or sack usually is in a kabadi scale photo (left, top, right, bottom as fractions).
# Cropping to it keeps the shop's background, identical across that shop's photos, out of the match.
LOAD_REGION = (0.2, 0.35, 0.8, 0.95)


def available() -> bool:
    """True when the optional dependencies are installed."""
    try:
        import numpy  # noqa: F401
        import onnxruntime  # noqa: F401
    except ImportError:
        return False
    return True


def model_path() -> str:
    return os.path.join(config.cache_dir(), "models", "dinov2-small.onnx")


def ensure_model() -> str:
    """Download the model once; refuse a file whose hash doesn't match the pinned one."""
    path = model_path()
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".part"
        urllib.request.urlretrieve(MODEL_URL, tmp)
        os.replace(tmp, path)
    with open(path, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    if digest != MODEL_SHA256:
        os.remove(path)
        raise RuntimeError(f"look-alike model hash mismatch ({digest[:12]}...); file removed, try again")
    return path


@lru_cache(maxsize=1)
def _session():
    import onnxruntime as ort

    return ort.InferenceSession(ensure_model(), providers=["CPUExecutionProvider"])


def _pixels(image_bytes: bytes, region: Optional[tuple] = LOAD_REGION):
    import numpy as np
    from PIL import Image

    im = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    if region:
        w, h = im.size
        im = im.crop((int(region[0] * w), int(region[1] * h), int(region[2] * w), int(region[3] * h)))
    scale = SIZE / min(im.size)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.BICUBIC)
    left, top = (im.width - CROP) // 2, (im.height - CROP) // 2
    im = im.crop((left, top, left + CROP, top + CROP))
    x = np.asarray(im, dtype=np.float32) / 255.0
    x = (x - np.array(MEAN, dtype=np.float32)) / np.array(STD, dtype=np.float32)
    return x.transpose(2, 0, 1)[None]          # 1 x 3 x 224 x 224


def embed(image_bytes: bytes, region: Optional[tuple] = LOAD_REGION):
    """A unit-length vector for the photo (by default only its load region): the image token and
    the mean patch token, joined. region=None embeds the whole photo."""
    import numpy as np

    tokens = _session().run(None, {"pixel_values": _pixels(image_bytes, region)})[0][0]   # (1 + patches) x 384
    v = np.concatenate([tokens[0], tokens[1:].mean(axis=0)])
    return v / np.linalg.norm(v)


def similarity(a, b) -> float:
    """Cosine similarity of two embeddings: 1.0 identical, around 0 unrelated."""
    import numpy as np

    return float(np.dot(a, b))


def similar_photos(photo: bytes, earlier: Iterable[tuple[str, object]], threshold: float,
                   limit: Optional[int] = 3) -> list[tuple[str, float]]:
    """Earlier photos (id, embedding) at least `threshold` similar to `photo`, most similar first."""
    v = embed(photo)
    hits = sorted(((pid, similarity(v, e)) for pid, e in earlier), key=lambda t: t[1], reverse=True)
    hits = [h for h in hits if h[1] >= threshold]
    return hits[:limit] if limit else hits
