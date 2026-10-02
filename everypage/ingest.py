"""Read a PDF page by page and record, for each page, HOW it was read and whether it worked.

A page with no text layer is a scan, not an empty page. A scan that was OCR'd sideways is
garbage that looks like text. Both are measured here, so nothing downstream has to guess.
"""
import json
import os
import re
import subprocess
import tempfile

MIN_TEXT_CHARS = 40      # below this a page's text layer is treated as absent
MIN_LEGIBILITY = 0.18    # share of tokens that are everyday words of the language
OCR_DPI = 300
OCR_LANG = os.environ.get("EVERYPAGE_OCR_LANG", "eng")

# The first version of this check counted "tokens with a vowel". A page OCR'd UPSIDE DOWN scored
# 0.96 on it, and a page blurred into mush scored 1.00, because nonsense like "pebueyoun" and
# "ee me oe" is full of vowels. Real prose is recognisable by its small words, so count those.
COMMON = set("""a about after all also an and any are as at be been before but by can could day did do each
for from had has have he her his if in into is it its may more most must no not of on one only or other our
out over shall she should so such than that the their them then there these they this to under up upon was
we were what when which who will with within would year you your said between agreement date amount paid pay
total page section party parties property price seller buyer signed name number address""".split())
EXTRA_WORDS = os.environ.get("EVERYPAGE_WORDS")   # optional file, one word per line, for other languages
if EXTRA_WORDS and os.path.exists(EXTRA_WORDS):
    with open(EXTRA_WORDS, encoding="utf-8") as _f:
        COMMON |= {w.strip().lower() for w in _f if w.strip()}

_TOKEN = re.compile(r"[A-Za-zÀ-ÿ]+")


def legibility(text):
    """Share of alphabetic tokens that are everyday words. Real prose sits near 0.3-0.5; noise near 0."""
    tokens = [t.lower() for t in _TOKEN.findall(text)]
    if len(tokens) < 8:
        return 0.0
    return sum(1 for t in tokens if t in COMMON) / len(tokens)


def _run(cmd, timeout=180):
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError("%s failed (rc=%d): %s" % (cmd[0], p.returncode, p.stderr.decode("utf-8", "replace")[:300]))
    return p.stdout


def page_count(pdf):
    out = _run(["pdfinfo", pdf]).decode("utf-8", "replace")
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    if not m:
        raise RuntimeError("pdfinfo gave no page count for %s" % pdf)
    return int(m.group(1))


def _text_layer(pdf, n):
    return _run(["pdftotext", "-layout", "-f", str(n), "-l", str(n), pdf, "-"]).decode("utf-8", "replace")


def _ocr(png, rotate):
    src = png
    if rotate:
        from PIL import Image
        src = png + ".r%d.png" % rotate
        Image.open(png).rotate(-rotate, expand=True).save(src)
    return _run(["tesseract", src, "-", "-l", OCR_LANG, "--psm", "3"], timeout=300).decode("utf-8", "replace")


def _ocr_page(pdf, n, tmp):
    base = os.path.join(tmp, "p%d" % n)
    _run(["pdftoppm", "-r", str(OCR_DPI), "-png", "-f", str(n), "-l", str(n), "-singlefile", pdf, base])
    png = base + ".png"
    best = (-1.0, "", 0)
    for rot in (0, 90, 270, 180):
        text = _ocr(png, rot)
        score = legibility(text)
        if score > best[0]:
            best = (score, text, rot)
        if score >= 0.30:      # clearly upright prose: stop rotating, each try costs CPU
            break
    return best


def read_pdf(pdf, progress=None):
    """Return {'file', 'pages': [...], 'total', 'readable', 'unreadable': [n, ...]}."""
    total = page_count(pdf)
    pages = []
    with tempfile.TemporaryDirectory() as tmp:
        for n in range(1, total + 1):
            page = {"n": n, "method": None, "rotation": 0, "legibility": 0.0, "chars": 0,
                    "status": "unreadable", "text": "", "error": None}
            try:
                text = _text_layer(pdf, n)
                if len(text.strip()) >= MIN_TEXT_CHARS:
                    page.update(method="text-layer", text=text, legibility=round(legibility(text), 2))
                else:
                    score, text, rot = _ocr_page(pdf, n, tmp)
                    page.update(method="ocr", text=text, rotation=rot, legibility=round(score, 2))
                page["chars"] = len(page["text"].strip())
                if page["chars"] >= MIN_TEXT_CHARS and page["legibility"] >= MIN_LEGIBILITY:
                    page["status"] = "ok"
            except Exception as e:  # a page that failed is reported, never silently dropped
                page["error"] = str(e)[:300]
            pages.append(page)
            if progress:
                progress(page, total)
    bad = [p["n"] for p in pages if p["status"] != "ok"]
    return {"file": os.path.abspath(pdf), "pages": pages, "total": total,
            "readable": total - len(bad), "unreadable": bad}


def cache_path(pdf):
    return pdf + ".everypage.json"


def load_or_read(pdf, progress=None, fresh=False):
    cp = cache_path(pdf)
    if not fresh and os.path.exists(cp) and os.path.getmtime(cp) >= os.path.getmtime(pdf):
        with open(cp, encoding="utf-8") as f:
            return json.load(f)
    doc = read_pdf(pdf, progress)
    with open(cp, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    return doc
