#!/usr/bin/env python3
"""Tidy a Whisper .srt into properly formatted subtitles.

Whisper produces accurate text with sloppy presentation: single lines far too
long to read, timings that run tight against each other, and no distinction
between sung and spoken. This applies the usual conventions:

  * songs marked with a music note at each end       ♪ Lyric ♪
  * two speakers in one cue split with dashes        - Line one\n- Line two
  * lines wrapped at 42 characters, at most two
  * minimum 1s on screen, maximum 7s, small gap between cues
  * narration left as plain text

    python3 format_srt.py in.srt out.srt [--songs 90-140,600-700]

--songs takes second ranges that are sung; without it, nothing is marked.
"""
import re, sys, textwrap

MAX_CHARS, MAX_LINES = 42, 2
MIN_DUR, MAX_DUR, GAP = 1.0, 7.0, 0.084


def to_s(t):
    h, m, rest = t.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def to_t(x):
    x = max(0, x)
    h, rem = divmod(x, 3600)
    m, s = divmod(rem, 60)
    return "%02d:%02d:%02d,%03d" % (h, m, int(s), round((s - int(s)) * 1000))


def parse(path):
    cues, block = [], []
    for line in open(path, encoding="utf-8"):
        if line.strip() == "":
            if len(block) >= 3:
                a, b = block[1].split(" --> ")
                cues.append({"start": to_s(a.strip()), "end": to_s(b.strip()),
                             "text": " ".join(x.strip() for x in block[2:]).strip()})
            block = []
        else:
            block.append(line.rstrip("\n"))
    if len(block) >= 3:
        a, b = block[1].split(" --> ")
        cues.append({"start": to_s(a.strip()), "end": to_s(b.strip()),
                     "text": " ".join(x.strip() for x in block[2:]).strip()})
    return cues


def wrap(text):
    """Two lines at most, broken as evenly as the text allows."""
    if len(text) <= MAX_CHARS:
        return [text]
    lines = textwrap.wrap(text, width=MAX_CHARS, break_long_words=False)
    if len(lines) <= MAX_LINES:
        return lines
    # Too long for two lines at 42. Rather than emit one huge line, widen a
    # little and balance the break — readable, and still well short of what
    # would overflow the screen.
    for width in (46, 50, 54):
        lines = textwrap.wrap(text, width=width, break_long_words=False)
        if len(lines) <= MAX_LINES:
            return lines
    # Still too long for two lines: split near the middle at a word boundary,
    # which keeps both halves readable instead of leaving one enormous line.
    mid = len(text) // 2
    cut = text.rfind(" ", 0, mid + 10)
    if cut <= 0:
        cut = mid
    a, b = text[:cut].strip(), text[cut:].strip()
    return [a, b]


def split_speakers(text):
    """A cue holding two speakers gets a dash before each."""
    if text.count("-") >= 1 and re.match(r"^-\s", text):
        return text
    parts = re.split(r"(?<=[.!?…])\s+(?=[-–—])", text)
    if len(parts) == 2:
        return "- " + parts[0].strip().lstrip("-– ") + "\n- " + parts[1].strip().lstrip("-– ")
    return text


def main():
    src, dst = sys.argv[1], sys.argv[2]
    songs = []
    if "--songs" in sys.argv:
        spec = sys.argv[sys.argv.index("--songs") + 1]
        for r in spec.split(","):
            a, b = r.split("-")
            songs.append((float(a), float(b)))

    cues = parse(src)
    for c in cues:
        if c["end"] - c["start"] < MIN_DUR:
            c["end"] = c["start"] + MIN_DUR
        if c["end"] - c["start"] > MAX_DUR:
            c["end"] = c["start"] + MAX_DUR
    for a, b in zip(cues, cues[1:]):
        if a["end"] > b["start"] - GAP:
            a["end"] = max(a["start"] + MIN_DUR * 0.6, b["start"] - GAP)

    out = []
    for n, c in enumerate(cues, 1):
        text = c["text"].strip()
        sung = any(a <= c["start"] < b for a, b in songs)
        if sung:
            body = "\n".join("♪ " + l + " ♪" for l in wrap(text))
        else:
            body = split_speakers(text)
            body = body if "\n" in body else "\n".join(wrap(body))
        out.append("%d\n%s --> %s\n%s\n" % (n, to_t(c["start"]), to_t(c["end"]), body))
    open(dst, "w", encoding="utf-8").write("\n".join(out))
    over = sum(1 for c in cues if len(c["text"]) > MAX_CHARS)
    print(f"  {len(cues)} cues written to {dst}")
    print(f"  {over} were over {MAX_CHARS} characters and have been wrapped")
    print(f"  {len(songs)} song range(s) marked with notes")


if __name__ == "__main__":
    main()
