# Contributing

Run the tests before and after a change; they need Poppler, Tesseract, Pillow and pytest, and no model:

    python3 -m pytest -q tests

To report a wrong answer, open an issue with the PDF (or a page of it, if you can share it), the exact
command you ran, the full output including the `COVERAGE:` line and the exit code, and what the right
answer was and on which page. A `CANNOT SAY` on a page you can read is a bug too; include the page.

Keep the three verdicts: the model never says "not found", the code does, and only after a complete read.
Do not add a retrieval step that lets the model skip pages.
