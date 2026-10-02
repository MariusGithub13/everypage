"""Answer a question from a document, with rules the model cannot talk its way around.

1. The model sees EVERY readable page, one at a time. No retrieval step decides what it may skip.
2. For each page it must return a verbatim quote. The code checks the quote is literally on that
   page; a quote that is not there is thrown away, whatever the model says about it.
3. The answer is written only from quotes that survived, and each carries its page number.
4. "It is not in the document" is never the model's sentence. The code says it, and only when
   every page was read. If any page was unreadable the verdict is CANNOT_SAY.
"""
import json

from . import llm
from .verdict import CANNOT_SAY, FOUND, NOT_FOUND, decide, quote_on_page

CHUNK = 2600

PAGE_PROMPT = """You are reading ONE page of a document for someone who asked a question.

QUESTION: {q}

PAGE {n} TEXT:
<<<
{text}
>>>

Does this page contain text that answers the question, fully or partly?
Reply with JSON only: {{"relevant": true or false, "quotes": ["exact sentence copied from the page", "..."]}}
Give up to three quotes, each one full sentence, copied character for character. Do not paraphrase.
If the page does not help, relevant is false and quotes is empty."""

ANSWER_PROMPT = """Answer the question using ONLY the quotes below. Each quote was checked and is really in the document.
Say which page each fact comes from, like (page 3). If the quotes disagree with each other, say so plainly and give both.
Do not add anything that is not in the quotes. Two to four short sentences, plain words.

QUESTION: {q}

QUOTES:
{quotes}

ANSWER:"""


def _chunks(text):
    text = text.strip()
    return [text[i:i + CHUNK] for i in range(0, len(text), CHUNK)] or [""]


def ask(doc, question, progress=None, generate=None):
    generate = generate or llm.generate
    evidence, rejected, examined = [], [], 0
    for p in doc["pages"]:
        if p["status"] != "ok":
            continue
        examined += 1
        for chunk in _chunks(p["text"]):
            raw = generate(PAGE_PROMPT.format(q=question, n=p["n"], text=chunk), as_json=True)
            try:
                r = json.loads(raw)
            except ValueError:
                r = {}
            if not isinstance(r, dict) or not r.get("relevant"):
                continue
            quotes = r.get("quotes") or ([r["quote"]] if r.get("quote") else [])
            for quote in [q.strip() for q in quotes if isinstance(q, str) and q.strip()][:3]:
                if quote_on_page(quote, p["text"]):
                    if not any(e["page"] == p["n"] and e["quote"] == quote for e in evidence):
                        evidence.append({"page": p["n"], "quote": quote, "method": p["method"]})
                else:
                    rejected.append({"page": p["n"], "quote": quote})
        if progress:
            progress(p, doc["total"])
    verdict = decide(evidence, doc)
    answer = None
    if verdict == FOUND:
        quotes = "\n".join('- (page %d) "%s"' % (e["page"], e["quote"]) for e in evidence)
        answer = generate(ANSWER_PROMPT.format(q=question, quotes=quotes)).strip()
    return {"verdict": verdict, "answer": answer, "evidence": evidence, "rejected": rejected,
            "examined": examined, "total": doc["total"], "unreadable": doc["unreadable"]}
