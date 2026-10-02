"""One small client for a local Ollama server. Nothing here can reach anything but localhost
unless you point EVERYPAGE_OLLAMA somewhere else yourself."""
import json
import os
import urllib.request

HOST = os.environ.get("EVERYPAGE_OLLAMA", "http://127.0.0.1:11434")
MODEL = os.environ.get("EVERYPAGE_MODEL", "gemma2:2b")


def generate(prompt, as_json=False, timeout=600):
    body = {"model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0, "num_ctx": 4096}}
    if as_json:
        body["format"] = "json"
    req = urllib.request.Request(HOST + "/api/generate", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["response"]
