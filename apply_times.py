#!/usr/bin/env python3
"""Put the real word-level timings onto the corrected text.

The text in beauty.srt has been corrected against the official lyrics and is
far better than any fresh transcription. The timings, though, came from
Whisper's 30-second processing blocks and can be seconds early.

Each corrected cue is matched to the word-timed segment whose text is closest,
and takes that segment's timing. Where a segment was split across two cues, the
span is divided in proportion to the text.
"""
import json, re, difflib

def norm(s):
    return re.sub(r"[^a-zà-ÿ ]", "", s.lower()).strip()

segs = json.load(open("word_times.json"))
blocks = open("beauty.srt", encoding="utf-8").read().strip().split("\n\n")

cues = []
for b in blocks:
    l = b.split("\n")
    if len(l) >= 3:
        cues.append({"text": l[2:], "flat": " ".join(l[2:])})

# walk both lists together — order is the same, so a local window suffices
si, applied, kept = 0, 0, 0
for c in cues:
    best, best_score, best_i = None, 0.0, si
    for j in range(si, min(si + 6, len(segs))):
        score = difflib.SequenceMatcher(None, norm(c["flat"]), norm(segs[j]["text"])).ratio()
        if score > best_score:
            best, best_score, best_i = segs[j], score, j
    if best and best_score > 0.45:
        c["a"], c["z"] = best["start"], best["end"]
        c["seg"] = best_i
        si = best_i
        applied += 1
    else:
        c["a"] = c["z"] = None
        kept += 1

# two cues sharing one segment split its span by text length
from collections import defaultdict
groups = defaultdict(list)
for i, c in enumerate(cues):
    if c.get("seg") is not None:
        groups[c["seg"]].append(i)
for seg, idxs in groups.items():
    if len(idxs) < 2:
        continue
    a, z = segs[seg]["start"], segs[seg]["end"]
    total = sum(len(cues[i]["flat"]) for i in idxs) or 1
    pos = a
    for i in idxs:
        share = (z - a) * len(cues[i]["flat"]) / total
        cues[i]["a"], cues[i]["z"] = pos, pos + share - 0.05
        pos += share

# fill any unmatched cue from its neighbours
for i, c in enumerate(cues):
    if c["a"] is None:
        prev = next((cues[j]["z"] for j in range(i - 1, -1, -1) if cues[j]["z"] is not None), 0)
        nxt = next((cues[j]["a"] for j in range(i + 1, len(cues)) if cues[j]["a"] is not None), prev + 2)
        c["a"], c["z"] = prev + 0.1, min(nxt - 0.1, prev + 2.5)

# reading speed, minimums, and no overlaps
CPS, MIN, MAX, GAP = 17.0, 1.0, 6.0, 0.08
for i, c in enumerate(cues):
    chars = len(c["flat"])
    want = max(MIN, min(MAX, chars / CPS + 0.45))
    if c["z"] - c["a"] < want:
        c["z"] = c["a"] + want
    if c["z"] - c["a"] > MAX:
        c["z"] = c["a"] + MAX
    if i + 1 < len(cues) and c["z"] > cues[i + 1]["a"] - GAP:
        c["z"] = max(c["a"] + MIN * 0.7, cues[i + 1]["a"] - GAP)

def f(x):
    x = max(0, x)
    h, rem = divmod(x, 3600)
    m, s = divmod(rem, 60)
    return "%02d:%02d:%02d,%03d" % (h, m, int(s), round((s - int(s)) * 1000))

out = ["%d\n%s --> %s\n%s" % (i, f(c["a"]), f(c["z"]), "\n".join(c["text"]))
       for i, c in enumerate(cues, 1)]
open("beauty.srt", "w", encoding="utf-8").write("\n\n".join(out) + "\n")
print(f"  {applied} cue(s) took a real word-level timing")
print(f"  {kept} had no confident match and were placed between their neighbours")
