#!/usr/bin/env python3
"""Correct Brazilian spellings and obvious Whisper artefacts in a .srt.

Whisper's training data is heavily Brazilian, so even a European Portuguese
soundtrack comes back with Brazilian orthography in places — génio written
gênio, and so on. It also invents text over music and silence.

    python3 fix_pt.py in.srt out.srt
"""
import re, sys

# Brazilian circumflex where European Portuguese takes an acute.
# Only words where the two varieties genuinely differ.
ACUTE = {
    "gênio": "génio", "gênios": "génios", "gênero": "género", "gêneros": "géneros",
    "gêmeo": "gémeo", "gêmeos": "gémeos", "gêmea": "gémea", "gêmeas": "gémeas",
    "tênis": "ténis", "fêmea": "fémea", "fêmeas": "fémeas",
    "econômico": "económico", "econômica": "económica", "econômicos": "económicos",
    "fenômeno": "fenómeno", "fenômenos": "fenómenos",
    "harmônico": "harmónico", "harmônica": "harmónica",
    "irônico": "irónico", "irônica": "irónica", "ironia": "ironia",
    "tônico": "tónico", "tônica": "tónica",
    "eletrônico": "electrónico", "eletrônica": "electrónica",
    "sinônimo": "sinónimo", "antônimo": "antónimo", "anônimo": "anónimo",
    "cônsul": "cónsul", "prêmio": "prémio", "prêmios": "prémios",
    "acadêmico": "académico", "acadêmica": "académica",
    "polêmico": "polémico", "polêmica": "polémica",
    "têrmo": "termo", "ônibus": "autocarro", "trem": "comboio",
    "geladeira": "frigorífico", "banheiro": "casa de banho",
    "café da manhã": "pequeno-almoço", "celular": "telemóvel",
    "xícara": "chávena", "grama": "relva", "time": "equipa",
}

# Lines Whisper produces over music, logos and silence.
JUNK = re.compile(
    r"^\s*(legendas?|subtitles?|transcri\w+|amara\.org|tradu\w+ por|"
    r"obrigad[oa] por (ver|assistir)|inscreva-se|www\.|http|"
    r"\[m[úu]sica\]|\(m[úu]sica\)|♪+\s*♪*|"
    r"a cidade no brasil|a cria[çc][ãa]o|o que [ée] isso\??)\s*$", re.I)


# Nothing is spoken before the narration begins; anything Whisper produces
# over the studio logo and opening music is invented.
SILENT_UNTIL = 58.0


def fix(text):
    for bad, good in ACUTE.items():
        text = re.sub(r"\b" + re.escape(bad) + r"\b", good, text, flags=re.I)
        cap = bad.capitalize()
        text = re.sub(r"\b" + re.escape(cap) + r"\b", good.capitalize(), text)
    return text


def main():
    src, dst = sys.argv[1], sys.argv[2]
    blocks = open(src, encoding="utf-8").read().strip().split("\n\n")
    out, dropped, changed = [], 0, 0
    for b in blocks:
        lines = b.split("\n")
        if len(lines) < 3:
            continue
        body = "\n".join(lines[2:])
        start = lines[1].split(" --> ")[0]
        h, m, rest = start.split(":")
        secs = int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))
        if secs < SILENT_UNTIL:
            dropped += 1
            continue
        if JUNK.match(body.strip()):
            dropped += 1
            continue
        new = fix(body)
        if new != body:
            changed += 1
        out.append(lines[0] + "\n" + lines[1] + "\n" + new)
    # renumber after any removals
    final = []
    for n, b in enumerate(out, 1):
        l = b.split("\n")
        final.append("\n".join([str(n)] + l[1:]))
    open(dst, "w", encoding="utf-8").write("\n\n".join(final) + "\n")
    print(f"  {len(blocks)} cues in, {len(final)} out")
    print(f"  {changed} cue(s) corrected, {dropped} junk cue(s) removed")


if __name__ == "__main__":
    main()
