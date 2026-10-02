"""The baseline everypage exists to beat: extract the text the usual way, hand it to the same
local model, ask the same question. No page accounting, no quote check."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from everypage import llm

pdf, question = sys.argv[1], sys.argv[2]
text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True).stdout.decode("utf-8", "replace")
print("NAIVE: pdftotext returned %d characters and no warning" % len(text.strip()))
print("NAIVE ANSWER: " + llm.generate(
    "Here is a document.\n<<<\n%s\n>>>\nAnswer in one or two sentences, from the document only.\nQUESTION: %s\nANSWER:"
    % (text, question)).strip())
