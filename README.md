# everypage

Ask a question about a PDF and get an answer that names its page, from a model that runs on your own machine.
If a page could not be read, it says so instead of saying "no".

It was built for one person: a friend with a folder of property papers, part printed, part scanned, some scanned
sideways. Her question is usually "does it say X anywhere?". The honest answers to that are three, not two.

| verdict | meaning | exit code |
|---|---|---|
| `FOUND` | here is the sentence, here is the page | 0 |
| `NOT FOUND` | every page was read, and it is not there | 1 |
| `CANNOT SAY` | it was not on the pages I could read, but some pages I could not read | 2 |

## What it does

```
python3 -m everypage read  FILE.pdf                # how each page was read, and whether it worked
python3 -m everypage find  FILE.pdf "18,450"       # exact text or number, every page, no model
python3 -m everypage ask   FILE.pdf "question"     # local model, every page, checked quotes
```

1. **Reads page by page and keeps the receipts.** A page with a text layer is read directly. A page without one is
   rendered and OCR'd. If the result does not look like language, it is retried at 90, 270 and 180 degrees and the
   best reading is kept. Each page ends as `OK` or `UNREADABLE`, and the coverage line is printed first, every time.
2. **Shows every readable page to the model, one at a time.** There is no retrieval step choosing which pages the
   model may skip. On a short legal document, the page a retriever skips is the addendum.
3. **Checks every quote in code.** The model must copy the sentence that answers the question. If that sentence is
   not literally on the page it named, it is discarded. The final answer is written only from quotes that survived.
4. **Never lets the model say "it is not there".** The code says it, and only after a complete read.

## Why local, why open

Property papers, family papers and medical papers are the documents people most need help reading and least want
to upload. The model here is [Gemma](https://ai.google.dev/gemma) (`gemma2:2b`, 1.6 GB) served by
[Ollama](https://ollama.com) on localhost, OCR is [Tesseract](https://github.com/tesseract-ocr/tesseract), PDF
handling is [Poppler](https://poppler.freedesktop.org). Nothing leaves the machine and it works with the network
cable out. A 2-billion-parameter model is enough because the code does the part that needs to be reliable: page
accounting, quote checking and the verdict. The model only has to point at a sentence.

Swap the model with `EVERYPAGE_MODEL=...`, the OCR language with `EVERYPAGE_OCR_LANG=...`, and add everyday words
of another language with `EVERYPAGE_WORDS=wordlist.txt`.

## Try it

```
sudo apt install poppler-utils tesseract-ocr     # or brew install poppler tesseract
ollama pull gemma2:2b
pip install pillow reportlab pytest               # only for the samples and the tests
python3 samples/make_samples.py                   # two invented 6-page agreements
./demo/run_demo.sh                                # output: demo/transcript.txt
python3 -m pytest -q tests                        # no model needed
```

The two sample PDFs are invented from the first word to the last: names, places, parcel number and amounts.
Pages 1 to 3 have a text layer, 4 and 5 are scans, and page 6 is a scan lying on its side. Page 6 is the only page
that mentions $18,450 of unpaid taxes. In the "damaged" copy, page 6 is blurred past reading.

## Limits, stated plainly

- It reads PDFs. Not Word files, not photos in a folder.
- The legibility check is a list of everyday English words. Another language needs its own list or pages will be
  marked unreadable, which is the safe direction to be wrong in.
- A page that is all numbers (a table with no prose) will be marked unreadable for the same reason.
- "Every page, one at a time" is slow on a CPU: roughly 15 to 20 seconds a page with `gemma2:2b` on one core.
- A verified quote proves the words are on the page. It does not prove the model understood them. Read the quote.
- This is a reading aid. It is not legal advice and it does not replace a lawyer reading the document.

MIT licence.
