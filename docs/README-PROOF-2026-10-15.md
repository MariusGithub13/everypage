# README proof, 15 October 2026

Every command in the README, run in order on a clean clone of `main` (commit `68912f5`), in a cloud
container: Ubuntu 24.04, Python 3.13.16, 4 CPU cores, no GPU, no Ollama installed, outbound network
limited to a short allow-list (PyPI and Ubuntu's apt mirrors reachable; `ollama.com` and GitHub
release downloads refused by the egress proxy with HTTP 403).

Legend: **passed** means the command exited as the README says and the output matched. **not run
here** means the container lacks something the command needs, with the reason. Nothing below is
inferred; every line of output was produced in this session.

## 1. `sudo apt install poppler-utils tesseract-ocr`

**Failed on the first try, passed after `apt update`.**

```
$ apt-get install -y poppler-utils tesseract-ocr
E: Unable to locate package tesseract-ocr
$ apt-get update && apt-get install -y poppler-utils tesseract-ocr
Setting up tesseract-ocr (5.3.4-1build5) ...
Setting up poppler-utils (24.02.0-1ubuntu9.10) ...
$ tesseract --version | head -1 ; pdftotext -v 2>&1 | head -1
tesseract 5.3.4
pdftotext version 24.02.0
```

A fresh Ubuntu image has no package index, so the README line fails until `apt update` has run.
README corrected to `sudo apt update && sudo apt install ...`.

## 2. `ollama pull gemma2:2b`

**Not run here.** Ollama is not installed and cannot be installed: the egress proxy refuses
`https://ollama.com/install.sh` and the GitHub release download (`CONNECT tunnel failed, response 403`).
`curl http://127.0.0.1:11434/api/tags` gets connection refused.

## 3. `pip install pillow reportlab pytest`

**Passed.** Pillow 12.3.0 and reportlab 5.0.1 were already present; pytest 9.1.1 was installed.

The comment on this line, "only for the samples and the tests", is not true for Pillow. `everypage/ingest.py`
imports `PIL.Image` to rotate a scanned page before retrying OCR. Measured by making `PIL` unimportable and
running `python3 -m everypage read samples/sale-agreement.pdf --fresh`:

```
COVERAGE: read 5 of 6 pages; could NOT read page(s) 6
  page 6   -              0 chars  legibility 0.00  UNREADABLE
[exit 2]
error recorded for page 6: "import of PIL halted; None in sys.modules"
```

With Pillow installed the same command reads 6 of 6 (see section 7). README corrected: Pillow is required;
reportlab and pytest are the optional ones.

## 4. `python3 samples/make_samples.py`

**Passed**, in 2.8 seconds, exit 0:

```
/home/user/everypage/samples/sale-agreement.pdf
/home/user/everypage/samples/sale-agreement-damaged.pdf
```

Two notes for a newcomer:

- The script rewrites the two PDFs that are committed in `samples/`. The new files differ byte for byte
  (PDF timestamps), so `git status` shows them modified. The tests pass on both the regenerated and the
  committed PDFs (section 6). The committed PDFs were restored before committing this proof.
- The script draws the scanned pages with a hard-coded font path,
  `/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf` (Debian and Ubuntu package `fonts-dejavu-core`). It
  will not run as written on macOS, where the README's `brew install` line points. README now says the
  step is optional because the PDFs are committed, and names the font.

## 5. `./demo/run_demo.sh`

**Not run here** (needs Ollama). It was started so the failure is on record. The model-free parts behave as
in `demo/transcript.txt`; every `ask` and the naive baseline stop at the first model call:

```
$ python3 demo/naive.py samples/sale-agreement.pdf Are there unpaid property taxes, how much, and who has to pay them?
NAIVE: pdftotext returned 1449 characters and no warning
[exit 1]

$ python3 -m everypage read samples/sale-agreement.pdf
COVERAGE: read 6 of 6 pages
  (six OK lines, identical to demo/transcript.txt)
[exit 0]

$ python3 -m everypage ask samples/sale-agreement.pdf Are there unpaid property taxes, how much, and who has to pay them?
COVERAGE: read 6 of 6 pages
[exit 1]
   stderr: urllib.error.URLError: <urlopen error [Errno 111] Connection refused>

$ python3 -m everypage find samples/sale-agreement-damaged.pdf 18,450
COVERAGE: read 5 of 6 pages; could NOT read page(s) 6
VERDICT: CANNOT SAY. Nothing found on the pages that were read, but page(s) 6 could not be read. This is NOT a 'no'.
[exit 2]
```

One thing worth knowing: when Ollama is not running, `ask` exits with code 1 after a Python traceback. Code 1
is also the README's `NOT FOUND` code. The README now says so, so nobody reads a connection failure as a
negative. The code is left as it is; changing exit codes is the author's call.

## 6. `python3 -m pytest -q tests`

**Passed**, twice: on the regenerated PDFs and on the committed PDFs.

```
$ python3 -m pytest -q tests
...........                                                              [100%]
11 passed in 26.72s      (regenerated samples)
11 passed in 26.18s      (committed samples)
```

The README says 11 tests pass. 11 tests pass.

## 7. The three commands under "What it does"

`read` and `find` need no model. **Passed**, output identical to `demo/transcript.txt`:

```
$ python3 -m everypage read samples/sale-agreement.pdf
COVERAGE: read 6 of 6 pages
  page 1   text-layer   591 chars  legibility 0.54  OK
  page 2   text-layer   446 chars  legibility 0.56  OK
  page 3   text-layer   408 chars  legibility 0.67  OK
  page 4   ocr          384 chars  legibility 0.48  OK
  page 5   ocr          225 chars  legibility 0.41  OK
  page 6   ocr          459 chars  legibility 0.68  rotated 90°  OK
[exit 0]

$ python3 -m everypage read samples/sale-agreement-damaged.pdf
COVERAGE: read 5 of 6 pages; could NOT read page(s) 6
  page 6   ocr          192 chars  legibility 0.10  rotated 270°  UNREADABLE
[exit 2]

$ python3 -m everypage find samples/sale-agreement.pdf "18,450"
COVERAGE: read 6 of 6 pages
  page 6 (ocr): 2024 remain unpaid in the total amount of $18,450. The Seller
  page 6 (ocr): taxes by closing, the Buyer may deduct $18,450 from the price
VERDICT: FOUND.
[exit 0]

$ python3 -m everypage find samples/sale-agreement-damaged.pdf "18,450"
COVERAGE: read 5 of 6 pages; could NOT read page(s) 6
VERDICT: CANNOT SAY. ...
[exit 2]

$ python3 -m everypage --help
usage: everypage [-h] [--fresh] {read,find,ask} pdf [query]
[exit 0]
```

`ask`: **not run here** (needs Ollama, see section 5). The `--fresh` flag and the `EVERYPAGE_MODEL`,
`EVERYPAGE_OCR_LANG`, `EVERYPAGE_WORDS` variables named in the README all exist in the code
(`cli.py`, `llm.py`, `ingest.py`).

## Claims checked without running a model

| README claim | Checked how | Result |
|---|---|---|
| Three verdicts with exit codes 0, 1, 2 | `cli.py`, `verdict.py`; `read` and `find` runs above | true |
| Pages 1 to 3 text layer, 4 and 5 scans, 6 sideways | `read` output | true |
| Page 6 is the only page with $18,450 | `find` output, `test_text_layer_alone_misses_half_the_document` | true |
| Damaged copy: page 6 unreadable | `read` on the damaged PDF | true |
| 11 tests pass, no model needed | pytest | true |
| "roughly 15 to 20 seconds a page" for `ask` | needs the model | not measured here, left as the author's number |
| Demo recording is a real run | needs the model | not re-run here; the model-free lines match the transcript |

## What changed in the README, and why

1. `sudo apt install` became `sudo apt update && sudo apt install`: the bare line fails on a fresh Ubuntu
   (section 1).
2. Pillow moved out of "only for the samples and the tests": it is needed to read a sideways scan (section 3).
3. The sample generator is marked optional and its font requirement is named (section 4).
4. One sentence on what `ask` does when Ollama is not running (section 5).
5. The Python version actually used here is stated; the README named none.

Nothing else in the README was changed. The measured numbers already there (legibility scores, 11 tests,
15 to 20 seconds a page) are the author's and were left alone.
