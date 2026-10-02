"""Exact search over EVERY page, done in code. No model is asked whether something is absent."""
import re

from .verdict import decide, digits, norm


def find(doc, needle):
    """Return (verdict, hits). A numeric needle matches regardless of separators."""
    hits = []
    is_number = bool(re.fullmatch(r"[\s$€£]*[\d][\d,.\s]*", needle.strip()))
    want = digits(needle) if is_number else norm(needle)
    for p in doc["pages"]:
        if p["status"] != "ok":
            continue
        for line in p["text"].splitlines():
            if not line.strip():
                continue
            if is_number:
                found = any(digits(tok) == want for tok in re.findall(r"\d[\d,.]*\d|\d", line))
            else:
                found = want in norm(line)
            if found:
                hits.append({"page": p["n"], "line": line.strip(), "method": p["method"]})
    return decide(hits, doc), hits
