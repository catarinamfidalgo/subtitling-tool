#!/usr/bin/env python3
"""Find and fix lines that are broken rather than merely misheard.

A wrong word is tolerable if the sentence still reads as Portuguese. A line
like "em troca de abrir contra o frio" is not — it teaches a learner a phrase
that does not exist. This fixes the ones that can be fixed mechanically and
lists the rest for a person to judge.

    python3 check_grammar.py in.srt out.srt      fix and report
    python3 check_grammar.py in.srt --report     report only
"""
import re, sys

# Confusions Whisper makes between words that sound alike, where only one
# reading is grammatical. Each is a whole phrase so context decides.
FIXES = [
    (r"\bem troca de abrir contra o frio\b", "em troca de abrigo contra o frio"),
    (r"\bde abrir contra o (frio|vento|tempo)\b", r"de abrigo contra o \1"),
    (r"\bem troca de abrir\b(?!\s+a\b)", "em troca de abrigo"),
    # gerund where the noun is meant
    (r"\buma velha pedindo\b", "uma velha pedinte"),
    (r"\bvelha pedindo\b", "velha pedinte"),
    # wrong gender/number on a noun
    (r"\bduelas de espadas?\b", "duelos de espadas"),
    # character names Whisper mangles — a learner would otherwise learn them wrong
    (r"\baquela Alê\b", "aquela Bela"),
    (r"\bAlê\b", "Bela"),
    (r"\bLef[óo]\b", "LeFou"),
    (r"\bLefu\b", "LeFou"),
    (r"\bangastou\b", "não é?"),
]

SUSPECT = [
    # preposition then a bare infinitive then another preposition
    (r"\b(de|em|para|com|por)\s+(abrir|fechar|correr|andar|ver|dar|pôr)\s+(contra|sobre|entre|dentro)\b",
     "preposition + infinitive where a noun belongs"),
    # article disagreeing with the following noun is usually a mishearing
    (r"\b(o)\s+(uma|umas)\b|\b(a)\s+(um|uns)\b", "article disagreement"),
    # gerund immediately after a noun, where Portugal uses a+infinitive or an
    # agent noun — a real grammar fault rather than a missing full stop
    (r"\b(um|uma|o|a)\s+\w+\s+\w+ndo\b(?!\s+(para|que|e))", "gerund after a noun"),
    # three or more repeats of the same short word
    (r"\b(\w{2,})(\s+\1){2,}\b", "word repeated three or more times"),
]


def blocks_of(path):
    return [b.split("\n") for b in open(path, encoding="utf-8").read().strip().split("\n\n")]


def main():
    src = sys.argv[1]
    report_only = "--report" in sys.argv
    dst = None if report_only else sys.argv[2]

    out, fixed, flagged = [], 0, []
    for b in blocks_of(src):
        if len(b) < 3:
            continue
        stamp, body = b[1], "\n".join(b[2:])
        new = body
        for pat, rep in FIXES:
            new = re.sub(pat, rep, new, flags=re.I)
        if new != body:
            fixed += 1
        for pat, why in SUSPECT:
            if re.search(pat, new, re.I | re.M):
                flagged.append((stamp.split(" --> ")[0], new, why))
                break
        out.append([b[0], stamp, new])

    print(f"  {fixed} line(s) corrected automatically")
    print(f"  {len(flagged)} line(s) need a human ear:\n")
    for t, txt, why in flagged[:40]:
        print(f"    {t}  [{why}]")
        print(f"       {txt[:100]}")
    if dst:
        open(dst, "w", encoding="utf-8").write(
            "\n\n".join("\n".join([str(n)] + b[1:]) for n, b in enumerate(out, 1)) + "\n")
        print(f"\n  written to {dst}")


if __name__ == "__main__":
    main()
