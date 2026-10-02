#!/bin/bash
# Reproduces demo/transcript.txt. Needs Ollama with gemma2:2b on localhost.
cd "$(dirname "$0")/.." || exit 1
Q1="Are there unpaid property taxes, how much, and who has to pay them?"
Q2="Does the agreement say anything about a broker commission?"
run(){ echo; echo "\$ $*"; "$@" 2>>demo/stderr.log; echo "[exit $?]"; }
run python3 demo/naive.py samples/sale-agreement.pdf "$Q1"
run python3 -m everypage read samples/sale-agreement.pdf
run python3 -m everypage ask samples/sale-agreement.pdf "$Q1"
run python3 -m everypage ask samples/sale-agreement.pdf "$Q2"
run python3 -m everypage ask samples/sale-agreement-damaged.pdf "$Q1"
run python3 -m everypage find samples/sale-agreement-damaged.pdf "18,450"
