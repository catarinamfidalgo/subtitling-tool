#!/usr/bin/env python3
"""Extract word-level timings from a film's audio.

Whisper's default output stamps each segment at its 30-second processing block,
so a line spoken at 1:17 can be stamped 1:00 — seventeen seconds early. Asking
for word timestamps instead gives the real position of the first and last word
of every segment.

This writes only timings. The text you already have is kept: once it has been
corrected by hand it is far better than a fresh transcription, so apply_times.py
lays these timings underneath it rather than replacing it.

    python3 retime.py FILM [-o word_times.json] [--lang pt] [--model large-v3]
"""
import argparse, json, os, sys


def main():
    p = argparse.ArgumentParser(
        description="Extract word-level timings from a film's audio.")
    p.add_argument("film", help="the film, or any file ffmpeg can read audio from")
    p.add_argument("-o", "--out", default="word_times.json",
                   help="where to write the timings (default: word_times.json)")
    p.add_argument("--lang", default="pt",
                   help="spoken language, as a Whisper code (default: pt)")
    p.add_argument("--model", default="large-v3",
                   help="Whisper model (default: large-v3)")
    a = p.parse_args()

    if not os.path.exists(a.film):
        sys.exit("no such file: %s" % a.film)

    import whisper  # imported late so --help works without it installed

    print("  loading %s…" % a.model)
    model = whisper.load_model(a.model)

    print("  listening to %s…" % os.path.basename(a.film))
    r = model.transcribe(a.film, language=a.lang, word_timestamps=True,
                         condition_on_previous_text=False, verbose=False)

    segs = []
    for s in r["segments"]:
        w = s.get("words") or []
        if not w:
            continue
        segs.append({
            "start": w[0]["start"],
            "end": w[-1]["end"],
            "text": s["text"].strip(),
            # Kept so a later pass can rank lines by how unsure Whisper was.
            "avg_logprob": s.get("avg_logprob"),
            "no_speech_prob": s.get("no_speech_prob"),
        })

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(segs, fh, ensure_ascii=False)

    print("  %d segments with real word timings -> %s" % (len(segs), a.out))


if __name__ == "__main__":
    main()
