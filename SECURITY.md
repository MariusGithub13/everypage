# Security

everypage runs on your own machine and talks only to a local Ollama at `127.0.0.1:11434` unless you
point `EVERYPAGE_OLLAMA` elsewhere. It shells out to `pdfinfo`, `pdftotext`, `pdftoppm` and `tesseract`
on the PDF you give it, so a crafted PDF reaches those programs with your user's rights.

To report a security problem, write to office@devaland.com with the version (commit), the command, and a
way to reproduce it. Please do not open a public issue for it. You will get an answer from a person; there
is no bug bounty.
