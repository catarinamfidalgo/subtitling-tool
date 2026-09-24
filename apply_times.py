#!/usr/bin/env python3
"""Put real word-level timings onto already-corrected subtitle text.

The text in a corrected .srt is worth keeping — once it has been checked by
hand it beats any fresh transcription. Its timings, though, came from Whisper's
30-second processing blocks and can be seconds early.

Each cue is matched to the word-timed segment whose text is closest, and takes
that segment's timing. Where one segment was split across two cues, its span is
divided between them in proportion to the text.

    python3 apply_times.py IN.srt word_times.json OUT.srt

IN and OUT may be the same path, in which case the file is rewritten in place.
"""
import argparse, json, os, re, sys, difflib
from collections import defaultdict

CPS = 17.0          # characters per second a viewer comfortably reads
MIN_DUR = 1.0
MAX_DUR = 6.0
GAP = 0.08
WINDOW = 6          # how far ahead to look for a matching segment
MATCH = 0.45        # below this the match is not trusted


def norm(s):
    return re.sub(r"[^a-zà-ÿ ]", "", s.lower()).strip()


def fmt(x):
    x = max(0, x)
    h, rem = divmod(x, 3600)
    m, s = divmod(rem, 60)
    return "%02d:%02d:%02d,%03d" % (h, m, int(s), round((s - int(s)) * 1000))


def read_cues(path):
    blocks = open(path, encoding="utf-8").read().strip().split("\n\n")
    cues = []
    for b in blocks:
        lines = b.split("\n")
        if len(lines) >= 3:
            cues.append({"text": lines[2:], "flat": " ".join(lines[2:])})
    return cues


def main():
    p = argparse.ArgumentParser(
        description="Apply word-level timings to corrected subtitle text.")
    p.add_argument("srt_in", help="the corrected .srt")
    p.add_argument("times", help="word_times.json, from retime.py")
    p.add_argument("srt_out", help="where to write (may equal srt_in)")
    a = p.parse_args()

    for f in (a.srt_in, a.times):
        if not os.path.exists(f):
            sys.exit("no such file: %s" % f)

    segs = json.load(open(a.times, encoding="utf-8"))
    cues = read_cues(a.srt_in)
    if not cues:
        sys.exit("no cues found in %s" % a.srt_in)

    # Walk both lists together — order is the same, so a local window suffices.
    si, applied, kept = 0, 0, 0
    for c in cues:
        best, best_score, best_i = None, 0.0, si
        for j in range(si, min(si + WINDOW, len(segs))):
            score = difflib.SequenceMatcher(
                None, norm(c["flat"]), norm(segs[j]["text"])).ratio()
            if score > best_score:
                best, best_score, best_i = segs[j], score, j
        if best and best_score > MATCH:
            c["a"], c["z"], c["seg"] = best["start"], best["end"], best_i
            si = best_i
            applied += 1
        else:
            c["a"] = c["z"] = None
            kept += 1

    # Two cues sharing one segment split its span by text length.
    groups = defaultdict(list)
    for i, c in enumerate(cues):
        if c.get("seg") is not None:
            groups[c["seg"]].append(i)
    for seg, idxs in groups.items():
        if len(idxs) < 2:
            continue
        a0, z0 = segs[seg]["start"], segs[seg]["end"]
        total = sum(len(cues[i]["flat"]) for i in idxs) or 1
        pos = a0
        for i in idxs:
            share = (z0 - a0) * len(cues[i]["flat"]) / total
            cues[i]["a"], cues[i]["z"] = pos, pos + share - 0.05
            pos += share

    # Fill any unmatched cue from its neighbours.
    for i, c in enumerate(cues):
        if c["a"] is None:
            prev = next((cues[j]["z"] for j in range(i - 1, -1, -1)
                         if cues[j]["z"] is not None), 0)
            nxt = next((cues[j]["a"] for j in range(i + 1, len(cues))
                        if cues[j]["a"] is not None), prev + 2)
            c["a"], c["z"] = prev + 0.1, min(nxt - 0.1, prev + 2.5)

    # Reading speed, minimums, and no overlaps.
    for i, c in enumerate(cues):
        want = max(MIN_DUR, min(MAX_DUR, len(c["flat"]) / CPS + 0.45))
        if c["z"] - c["a"] < want:
            c["z"] = c["a"] + want
        if c["z"] - c["a"] > MAX_DUR:
            c["z"] = c["a"] + MAX_DUR
        if i + 1 < len(cues) and c["z"] > cues[i + 1]["a"] - GAP:
            c["z"] = max(c["a"] + MIN_DUR * 0.7, cues[i + 1]["a"] - GAP)

    out = ["%d\n%s --> %s\n%s" % (i, fmt(c["a"]), fmt(c["z"]), "\n".join(c["text"]))
           for i, c in enumerate(cues, 1)]
    with open(a.srt_out, "w", encoding="utf-8") as fh:
        fh.write("\n\n".join(out) + "\n")

    print("  %d cue(s) took a real word-level timing" % applied)
    print("  %d had no confident match and were placed between their neighbours" % kept)
    print("  -> %s" % a.srt_out)


if __name__ == "__main__":
    main()
