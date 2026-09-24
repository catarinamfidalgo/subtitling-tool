#!/usr/bin/env python3
"""Re-time the subtitles from word-level timestamps.

Whisper's default output stamps each segment at its 30-second processing block,
so a line spoken at 1:17 can be stamped 1:00 — seventeen seconds early. Asking
for word timestamps gives the real position of the first and last word.

The existing text is kept: it has been corrected against the official lyrics
and is far better than a fresh transcription. Only the timings are replaced.
"""
import whisper, json, sys

model = whisper.load_model("large-v3")
r = model.transcribe("beauty.mp4", language="pt", word_timestamps=True,
                     condition_on_previous_text=False, verbose=False)
segs = []
for s in r["segments"]:
    w = s.get("words") or []
    if not w:
        continue
    segs.append({"start": w[0]["start"], "end": w[-1]["end"], "text": s["text"].strip()})
json.dump(segs, open("word_times.json", "w"))
print(f"  {len(segs)} segments with real word timings")
