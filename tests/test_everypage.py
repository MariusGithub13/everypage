"""No model needed: the model is replaced by a stub, because the rules under test are the CODE's."""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from everypage import ask as ask_mod              # noqa: E402
from everypage.find import find                   # noqa: E402
from everypage.ingest import legibility, load_or_read   # noqa: E402
from everypage.verdict import CANNOT_SAY, FOUND, NOT_FOUND, digits, quote_on_page  # noqa: E402

GOOD = os.path.join(ROOT, "samples", "sale-agreement.pdf")
BAD = os.path.join(ROOT, "samples", "sale-agreement-damaged.pdf")


@pytest.fixture(scope="session")
def good():
    return load_or_read(GOOD)


@pytest.fixture(scope="session")
def bad():
    return load_or_read(BAD)


def test_every_page_is_read_including_the_sideways_scan(good):
    assert good["total"] == 6 and good["readable"] == 6 and good["unreadable"] == []
    assert [p["method"] for p in good["pages"]] == ["text-layer"] * 3 + ["ocr"] * 3
    assert good["pages"][5]["rotation"] in (90, 270)


def test_upside_down_and_mush_are_not_legible():
    assert legibility("pebueyoun urewel JuoweeIby oY Jo SULI9 [[V OD A}WOoItTp Ayunod oy Aed pue aod ey WO") < 0.18
    assert legibility("ee ee mee ON me mere me al nt mw ee ee ee eng oe fee ee ae eet oe em me oe ewe") < 0.18
    assert legibility("The Seller shall pay this amount in full before the closing of the sale.") > 0.3


def test_damaged_page_is_reported_not_hidden(bad):
    assert bad["unreadable"] == [6] and bad["readable"] == 5


def test_text_layer_alone_misses_half_the_document():
    out = subprocess.run(["pdftotext", GOOD, "-"], capture_output=True).stdout.decode()
    assert "18,450" not in out and "ADDENDUM" not in out


def test_find_number_any_format(good):
    for needle in ("18,450", "18450", "$18,450.00"):
        verdict, hits = find(good, needle)
        assert verdict == FOUND and {h["page"] for h in hits} == {6}


def test_find_negative_needs_a_complete_read(good, bad):
    assert find(good, "broker commission")[0] == NOT_FOUND
    assert find(bad, "broker commission")[0] == CANNOT_SAY
    assert find(bad, "18,450")[0] == CANNOT_SAY          # it IS there, on the page nobody could read


def test_digits():
    assert digits("$2,100,000.00") == digits("2100000") == "2100000"
    assert digits("18,450.") == "18450"


def test_quote_must_be_on_the_page():
    page = "The Seller shall pay this amount\nin full before closing."
    assert quote_on_page("the seller shall pay this amount in full before closing.", page)
    assert not quote_on_page("The Buyer shall pay this amount in full", page)


def _stub(reply_for_page):
    def generate(prompt, as_json=False, timeout=0):
        if not as_json:
            return "stub answer"
        n = int(prompt.split("PAGE ")[1].split(" ")[0])
        return json.dumps(reply_for_page(n))
    return generate


def test_invented_quote_is_discarded(good):
    r = ask_mod.ask(good, "q", generate=_stub(lambda n: {"relevant": True, "quotes": ["The Buyer owes a penalty of $99,000."]}))
    assert r["evidence"] == [] and len(r["rejected"]) == 6 and r["verdict"] == NOT_FOUND


def test_real_quote_survives_with_its_page(good):
    q = "The Seller shall pay this amount in full before closing."
    r = ask_mod.ask(good, "q", generate=_stub(lambda n: {"relevant": n == 6, "quotes": [q] if n == 6 else []}))
    assert r["verdict"] == FOUND and r["evidence"] == [{"page": 6, "quote": q, "method": "ocr"}]


def test_model_saying_no_on_a_damaged_document_is_cannot_say(bad):
    r = ask_mod.ask(bad, "q", generate=_stub(lambda n: {"relevant": False, "quotes": []}))
    assert r["verdict"] == CANNOT_SAY and r["examined"] == 5 and r["unreadable"] == [6]
