#!/usr/bin/env python3
"""Tighten subtitle timings.

The earlier pass clamped every cue to a maximum of 7 seconds, which left short
lines sitting on screen for the whole of it — appearing before the line is
spoken and lingering afterwards. Reading speed is what should decide: roughly
17 characters per second, with a floor so nothing flashes past.

    python3 fix_timing.py in.srt out.srt
"""
import sys

CPS = 17.0          # characters per second a viewer comfortably reads
MIN_DUR = 1.1
MAX_DUR = 6.0
LEAD = 0.15         # a cue may start this far before the audio, no more
GAP = 0.09


def s(t):
    h, m, r = t.split(":")
    sec, ms = r.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


def f(x):
    x = max(0, x)
    h, rem = divmod(x, 3600)
    m, sec = divmod(rem, 60)
    return "%02d:%02d:%02d,%03d" % (h, m, int(sec), round((sec - int(sec)) * 1000))


blocks = open(sys.argv[1], encoding="utf-8").read().strip().split("\n\n")
cues = []
for b in blocks:
    l = b.split("\n")
    if len(l) < 3:
        continue
    a, z = [x.strip() for x in l[1].split(" --> ")]
    cues.append({"n": l[0], "a": s(a), "z": s(z), "text": l[2:]})

shortened = 0
for i, c in enumerate(cues):
    chars = sum(len(x) for x in c["text"])
    want = max(MIN_DUR, min(MAX_DUR, chars / CPS + 0.4))
    have = c["z"] - c["a"]
    if have > want + 0.3:
        c["z"] = c["a"] + want
        shortened += 1
    # never run into the next cue
    if i + 1 < len(cues) and c["z"] > cues[i + 1]["a"] - GAP:
        c["z"] = max(c["a"] + MIN_DUR, cues[i + 1]["a"] - GAP)

out = []
for i, c in enumerate(cues, 1):
    out.append("%d\n%s --> %s\n%s" % (i, f(c["a"]), f(c["z"]), "\n".join(c["text"])))
open(sys.argv[2], "w", encoding="utf-8").write("\n\n".join(out) + "\n")

durs = [c["z"] - c["a"] for c in cues]
print(f"  {shortened} cue(s) shortened to match their reading time")
print(f"  longest now {max(durs):.1f}s, average {sum(durs)/len(durs):.1f}s")
