import asyncio
import io
import os
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from PIL import Image

import bot.telegram_bot as tb
from bot import strings_hi
from bot.cards import make_receipt_card

ROOT = Path(__file__).resolve().parent.parent


def _cbs(markup):
    return [b.callback_data for row in markup.inline_keyboard for b in row]


def test_keypad_append_dot_back():
    assert tb.apply_keypad("", "5") == "5"
    assert tb.apply_keypad("", ".") == "0."
    assert tb.apply_keypad("12", ".") == "12."
    assert tb.apply_keypad("12", "back") == "1"
    assert tb.apply_keypad("", "back") == ""
    assert tb.apply_keypad("1", "zzz") == "1"


def test_keypad_double_dot_and_cap():
    assert tb.apply_keypad("1.5", ".") == "1.5"
    assert tb.apply_keypad("123456", "7") == "123456"
    assert tb.apply_keypad("12345", ".") == "12345."
    assert tb.apply_keypad("123456", ".") == "123456"


def test_parse_kg():
    assert tb.parse_kg("12.5") == 12.5
    assert tb.parse_kg("500") == 500.0
    for bad in ["0", "0.0", "501", "", "abc", "nan", "1e3", "1_0", "1.", "-3", "inf"]:
        assert tb.parse_kg(bad) is None, bad


def test_build_payload():
    p = tb.build_payload(42, "seelampur", "PET", 3, True, "abc")
    assert p == {"collector_id": "kab_42", "locality": "seelampur",
                 "taps": {"material": "PET", "kg": 3.0}, "photo_b64": "abc", "simulate": "mismatch"}
    q = tb.build_payload(42, "seelampur", "PET", 3, False)
    assert q["simulate"] is None and q["photo_b64"] is None


def test_resize_for_upload_rgb_jpeg_big():
    buf = io.BytesIO()
    Image.new("RGBA", (3000, 1500), (255, 0, 0, 128)).save(buf, format="PNG")
    out = tb.resize_for_upload(buf.getvalue())
    img = Image.open(io.BytesIO(out))
    assert img.format == "JPEG" and img.mode == "RGB"
    assert max(img.size) <= 1024


def test_keyboards():
    loc = _cbs(tb.locality_keyboard())
    assert len(loc) == len(tb.LOCALITIES) and all(c.startswith("loc:") for c in loc)
    mat = _cbs(tb.material_keyboard())
    assert len(mat) == len(strings_hi.MATERIAL_ORDER) and all(c.startswith("mat:") for c in mat)
    kg = _cbs(tb.kg_keyboard())
    assert len(kg) == 13 and all(c.startswith("kg:") for c in kg)
    assert "kg:back" in kg and "kg:ok" in kg and "kg:." in kg


def test_contract_payload_to_card():
    p = tb.build_payload(1, "seelampur", "PET", 5.5, False)
    resp = tb.api.collect(p)
    assert resp["status"] == "receipt"
    assert make_receipt_card(resp["receipt"]).startswith(b"\x89PNG\r\n\x1a\n")


def test_all_used_string_keys_exist():
    src = (ROOT / "bot" / "telegram_bot.py").read_text(encoding="utf-8")
    keys = set(re.findall(r'\bt\(\s*"([a-z_]+)"', src)) | {"demo_on", "demo_off"}
    assert keys
    for k in keys:
        assert k in strings_hi.HI and k in strings_hi.EN, k


def test_env_loader_bom_and_comment(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_bytes("﻿# comment\n\nKK_TEST_TOKEN=abc123\nKK_KEEP=new\n".encode("utf-8"))
    monkeypatch.delenv("KK_TEST_TOKEN", raising=False)
    monkeypatch.setenv("KK_KEEP", "old")
    tb.load_env(f)
    assert os.environ["KK_TEST_TOKEN"] == "abc123"
    assert os.environ["KK_KEEP"] == "old"
    monkeypatch.delenv("KK_TEST_TOKEN", raising=False)


def test_import_without_token():
    env = {k: v for k, v in os.environ.items() if k != "TELEGRAM_BOT_TOKEN"}
    r = subprocess.run([sys.executable, "-c", "import bot.telegram_bot"], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def _cb_update(data):
    update = MagicMock()
    update.callback_query.data = data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    msg = MagicMock()
    msg.reply_text = AsyncMock()
    msg.reply_photo = AsyncMock()
    update.effective_message = msg
    update.effective_user.id = 7
    return update, msg


def _ctx(ud):
    c = MagicMock()
    c.user_data = ud
    return c


def test_material_tap_shows_keypad():
    ud = {"name": "Raju", "locality": "seelampur", "state": "choosing_material",
          "pending": {"material": None, "kg_buf": "", "photo_b64": None}}
    update, msg = _cb_update("mat:PET")
    asyncio.run(tb.material_cb(update, _ctx(ud)))
    update.callback_query.answer.assert_awaited_once()
    assert ud["pending"]["material"] == "PET" and ud["state"] == "entering_kg"
    assert _cbs(msg.reply_text.await_args.kwargs["reply_markup"]) == _cbs(tb.kg_keyboard())


def test_kg_ok_collects_and_sends_receipt():
    ud = {"name": "Raju", "locality": "seelampur", "state": "entering_kg",
          "pending": {"material": "PET", "kg_buf": "12.5", "photo_b64": None}}
    update, msg = _cb_update("kg:ok")
    asyncio.run(tb.keypad_cb(update, _ctx(ud)))
    msg.reply_photo.assert_awaited_once()
    assert msg.reply_photo.await_args.kwargs["photo"].startswith(b"\x89PNG")
    assert ud["state"] == "ready"


def test_kg_ok_mismatch_demo_fires_once():
    ud = {"name": "Raju", "locality": "seelampur", "state": "entering_kg", "simulate_mismatch": True,
          "pending": {"material": "PET", "kg_buf": "20", "photo_b64": None}}
    update, msg = _cb_update("kg:ok")
    asyncio.run(tb.keypad_cb(update, _ctx(ud)))
    msg.reply_photo.assert_not_awaited()
    assert ud["state"] == "awaiting_answer" and ud["simulate_mismatch"] is False


def test_kg_ok_invalid_stays():
    ud = {"name": "Raju", "locality": "seelampur", "state": "entering_kg",
          "pending": {"material": "PET", "kg_buf": "", "photo_b64": None}}
    update, msg = _cb_update("kg:ok")
    asyncio.run(tb.keypad_cb(update, _ctx(ud)))
    assert ud["state"] == "entering_kg"
    assert msg.reply_text.await_args.args[0] == strings_hi.t("bad_weight")


def test_hisaab_sends_income_image():
    ud = {"name": "Raju", "locality": "seelampur", "state": "ready"}
    update, msg = _cb_update("")  # provides effective_message + effective_user.id
    asyncio.run(tb.hisaab_cmd(update, _ctx(ud)))
    msg.reply_photo.assert_awaited_once()
    assert msg.reply_photo.await_args.kwargs["photo"][:8] == b"\x89PNG\r\n\x1a\n"


def test_hisaab_before_registration():
    update, msg = _cb_update("")
    asyncio.run(tb.hisaab_cmd(update, _ctx({})))
    msg.reply_photo.assert_not_awaited()
    assert msg.reply_text.await_args.args[0] == strings_hi.t("need_start")


def test_unregistered_callback_routes_to_start():
    ud = {}
    update, msg = _cb_update("mat:PET")
    asyncio.run(tb.material_cb(update, _ctx(ud)))
    assert ud["state"] == "need_name"
    assert msg.reply_text.await_args_list[0].args[0] == strings_hi.t("need_start")


# ---- voice notes (photo, then a voice note replaces the taps) ----
def _voice_update(ogg=b"OggSfake-voice-bytes"):
    update = MagicMock()
    msg = MagicMock()
    msg.reply_text = AsyncMock()
    msg.reply_photo = AsyncMock()
    f = MagicMock()
    f.download_as_bytearray = AsyncMock(return_value=bytearray(ogg))
    msg.voice.get_file = AsyncMock(return_value=f)
    update.effective_message = msg
    update.effective_user.id = 7
    return update, msg


def test_build_payload_voice_has_audio_no_taps():
    p = tb.build_payload(42, "seelampur", None, None, False, "photo", audio_b64="AUD")
    assert p["audio_b64"] == "AUD"
    assert p.get("taps") is None
    assert p["photo_b64"] == "photo"
    # the tap path is unchanged: taps present, no audio_b64 key
    q = tb.build_payload(42, "seelampur", "PET", 3, False, "photo")
    assert q["taps"] == {"material": "PET", "kg": 3.0} and "audio_b64" not in q


def test_voice_unregistered_asks_start():
    update, msg = _voice_update()
    asyncio.run(tb.voice_handler(update, _ctx({})))
    msg.reply_photo.assert_not_awaited()
    assert msg.reply_text.await_args.args[0] == strings_hi.t("need_start")


def test_voice_without_photo_asks_for_photo():
    ud = {"name": "Raju", "locality": "seelampur", "state": "ready",
          "pending": {"material": None, "kg_buf": "", "photo_b64": None}}
    update, msg = _voice_update()
    asyncio.run(tb.voice_handler(update, _ctx(ud)))
    msg.reply_photo.assert_not_awaited()
    assert msg.reply_text.await_args.args[0] == strings_hi.t("send_photo")


def test_voice_with_photo_sends_audio_and_returns_receipt(monkeypatch):
    captured = {}
    real = tb.api.collect

    def spy(payload):
        captured["payload"] = payload
        return real(payload)

    monkeypatch.setattr(tb.api, "collect", spy)
    ud = {"name": "Raju", "locality": "seelampur", "state": "choosing_material",
          "pending": {"material": None, "kg_buf": "", "photo_b64": "PHOTOB64"}}
    update, msg = _voice_update()
    asyncio.run(tb.voice_handler(update, _ctx(ud)))

    # the voice note was downloaded, base64'd, and sent as audio_b64 with no taps
    assert captured["payload"].get("audio_b64")
    assert captured["payload"].get("taps") is None
    assert captured["payload"]["photo_b64"] == "PHOTOB64"
    # a receipt card came back and the flow reset to ready
    msg.reply_photo.assert_awaited_once()
    assert msg.reply_photo.await_args.kwargs["photo"].startswith(b"\x89PNG")
    assert ud["state"] == "ready"


# ---- language: English / Hinglish / Devanagari Hindi ----
def _is_devanagari(s):
    return any("ऀ" <= ch <= "ॿ" for ch in s)


def test_hi_dev_table_covers_all_keys_and_is_devanagari():
    assert set(strings_hi.HI_DEV) == set(strings_hi.HI) == set(strings_hi.EN)
    assert _is_devanagari(strings_hi.HI_DEV["welcome"])


def test_t_three_languages():
    assert strings_hi.t("ask_name", lang="en") == strings_hi.EN["ask_name"]
    assert strings_hi.t("ask_name", lang="hi") == strings_hi.HI["ask_name"]
    assert strings_hi.t("ask_name", lang="hi_dev") == strings_hi.HI_DEV["ask_name"]


def test_t_uses_contextvar_when_no_lang():
    try:
        strings_hi.set_lang("en")
        assert strings_hi.t("ask_name") == strings_hi.EN["ask_name"]
        strings_hi.set_lang("hi_dev")
        assert strings_hi.t("ask_name") == strings_hi.HI_DEV["ask_name"]
    finally:
        strings_hi.set_lang(strings_hi.LANG_DEFAULT)


def test_material_label_devanagari():
    lbl = strings_hi.material_label("PET", lang="hi_dev")
    assert lbl == strings_hi.MATERIAL_LABELS["PET"]["hi_dev"]
    assert _is_devanagari(lbl)


def test_start_asks_language_first():
    ud = {}
    update, msg = _cb_update("")
    asyncio.run(tb.start(update, _ctx(ud)))
    assert ud["state"] == "need_language"
    cbs = _cbs(msg.reply_text.await_args.kwargs["reply_markup"])
    assert set(cbs) == {"lang:en", "lang:hi", "lang:hi_dev"}


def test_language_pick_sets_lang_and_asks_name_in_that_language():
    ud = {"pending": {"material": None, "kg_buf": "", "photo_b64": None}}
    update, msg = _cb_update("lang:en")
    asyncio.run(tb.language_cb(update, _ctx(ud)))
    assert ud["lang"] == "en" and ud["state"] == "need_name"
    texts = [c.args[0] for c in msg.reply_text.await_args_list]
    assert strings_hi.EN["ask_name"] in texts


def test_safe_wrapper_applies_user_language():
    ud = {"lang": "en"}
    update, msg = _cb_update("")
    asyncio.run(tb.help_cmd(update, _ctx(ud)))
    assert msg.reply_text.await_args.args[0] == strings_hi.EN["help"]
