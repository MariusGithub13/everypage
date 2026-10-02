"""everypage read FILE.pdf | find FILE.pdf "text or number" | ask FILE.pdf "question"

Exit codes: 0 = answered from a complete read, 1 = not found in a complete read,
2 = cannot say (a page could not be read) or the read failed. Three states, never two.
"""
import argparse
import sys

from . import ask as ask_mod
from . import find as find_mod
from .ingest import load_or_read
from .verdict import CANNOT_SAY, FOUND, NOT_FOUND, coverage_line


def _progress(page, total):
    how = page["method"] or "failed"
    extra = ", rotated %d°" % page["rotation"] if page["rotation"] else ""
    sys.stderr.write("  page %d/%d: %s%s, legibility %.2f, %s\n"
                     % (page["n"], total, how, extra, page["legibility"], page["status"]))


def _asked(page, total):
    sys.stderr.write("  asked page %d/%d\n" % (page["n"], total))


def _exit(verdict):
    return {FOUND: 0, NOT_FOUND: 1, CANNOT_SAY: 2}[verdict]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="everypage", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["read", "find", "ask"])
    ap.add_argument("pdf")
    ap.add_argument("query", nargs="?")
    ap.add_argument("--fresh", action="store_true", help="ignore the cached read")
    a = ap.parse_args(argv)
    if a.command != "read" and not a.query:
        ap.error("%s needs a query" % a.command)

    doc = load_or_read(a.pdf, _progress, a.fresh)
    print("COVERAGE: " + coverage_line(doc))

    if a.command == "read":
        for p in doc["pages"]:
            print("  page %-3d %-10s %5d chars  legibility %.2f%s  %s" % (
                p["n"], p["method"] or "-", p["chars"], p["legibility"],
                "  rotated %d°" % p["rotation"] if p["rotation"] else "", p["status"].upper()))
        return 2 if doc["unreadable"] else 0

    if a.command == "find":
        verdict, hits = find_mod.find(doc, a.query)
        for h in hits:
            print('  page %d (%s): %s' % (h["page"], h["method"], h["line"]))
    else:
        r = ask_mod.ask(doc, a.query, _asked)
        verdict = r["verdict"]
        if r["answer"]:
            print("ANSWER: " + r["answer"])
        for e in r["evidence"]:
            print('  page %d (%s): "%s"' % (e["page"], e["method"], e["quote"]))
        if r["rejected"]:
            print("  (%d quote(s) the model offered were NOT on the page it named and were discarded)"
                  % len(r["rejected"]))

    if verdict == NOT_FOUND:
        print("VERDICT: NOT FOUND. All %d of %d pages were read, so this is a real negative."
              % (doc["readable"], doc["total"]))
    elif verdict == CANNOT_SAY:
        print("VERDICT: CANNOT SAY. Nothing found on the pages that were read, but page(s) %s could not "
              "be read. This is NOT a 'no'." % ", ".join(str(n) for n in doc["unreadable"]))
    else:
        print("VERDICT: FOUND.")
    return _exit(verdict)


if __name__ == "__main__":
    sys.exit(main())
