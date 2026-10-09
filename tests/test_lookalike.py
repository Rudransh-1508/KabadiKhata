import io

import pytest

np = pytest.importorskip("numpy")
from PIL import Image  # noqa: E402

from perception import lookalike  # noqa: E402


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("KK_CACHE_DIR", str(tmp_path))
    lookalike._session.cache_clear()
    yield
    lookalike._session.cache_clear()


def png(w=400, h=300, color=(200, 50, 50)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def test_pixels_are_dinov2_shaped_and_normalised():
    x = lookalike._pixels(png())
    assert x.shape == (1, 3, 224, 224) and x.dtype == np.float32
    whole = lookalike._pixels(png(), region=None)
    assert whole.shape == (1, 3, 224, 224)


def test_similar_photos_ranks_and_thresholds(monkeypatch):
    unit = lambda *v: np.array(v, dtype=np.float32) / np.linalg.norm(v)  # noqa: E731
    monkeypatch.setattr(lookalike, "embed", lambda raw, region=lookalike.LOAD_REGION: unit(1, 0))
    earlier = [("KK-A", unit(1, 0.1)), ("KK-B", unit(0, 1)), ("KK-C", unit(1, 0.4))]
    hits = lookalike.similar_photos(b"photo", earlier, threshold=0.9)
    assert [h[0] for h in hits] == ["KK-A", "KK-C"]
    assert hits[0][1] > hits[1][1]
    assert lookalike.similar_photos(b"photo", earlier, threshold=0.9, limit=1)[0][0] == "KK-A"


def test_a_model_file_with_the_wrong_hash_is_refused(monkeypatch):
    def fake_download(url, path):
        with open(path, "wb") as fh:
            fh.write(b"not the model")

    monkeypatch.setattr(lookalike.urllib.request, "urlretrieve", fake_download)
    with pytest.raises(RuntimeError, match="hash mismatch"):
        lookalike.ensure_model()
    assert not __import__("os").path.exists(lookalike.model_path())  # removed, so the next try re-downloads


def test_model_is_pinned():
    assert lookalike.MODEL_REVISION in lookalike.MODEL_URL
    assert len(lookalike.MODEL_SHA256) == 64
