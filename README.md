# Subtitling tool

Subtitle a film from its own audio easily.

Point it at a film, get subtitles back: text transcribed from the soundtrack,
cut into readable lines, and timed to the moment each line is actually spoken.
Written for European Portuguese, and for subtitles accurate enough to learn the
language from.

Whisper gets you most of the way and then leaves three problems it cannot see:
it writes Brazilian orthography, it stamps timings at the wrong place, and it
occasionally invents Portuguese that does not exist. A wrong word is survivable
— a learner shrugs past it. A line like *"em troca de abrir contra o frio"* is
not: it teaches a phrase nobody says. These scripts fix what can be fixed
mechanically and list the rest for a person to judge.

Work in progress.

## The pipeline

Transcribe first, with Whisper `large-v3`, then:

| Step | Script | What it does |
|---|---|---|
| 1 | `format_srt.py` | Presentation. Wraps at 42 characters, two lines maximum, 1–7s on screen, marks songs `♪ … ♪`, splits two speakers with dashes. |
| 2 | `fix_pt.py` | Brazilian → European orthography (*gênio* → *génio*, *trem* → *comboio*), and strips text Whisper invents over music and silence. |
| 3 | `check_grammar.py` | Lines that are broken rather than merely misheard. Fixes the mechanical ones, reports the rest. `--report` to look without changing. |
| 4 | `retime.py` | Re-runs Whisper asking for **word-level** timestamps → `word_times.json`. |
| 5 | `apply_times.py` | Puts those real timings onto the corrected text, matching cue to segment by closest text. |
| 6 | `fix_timing.py` | Timing by reading speed — ~17 characters/second, 1.1–6s, rather than one flat maximum. |

Steps 4–6 exist because Whisper stamps each segment at its 30-second processing
block, so a line spoken at 1:17 arrives stamped 1:00. The text from steps 1–3 is
worth keeping — it has been corrected by hand — so the timings are replaced
underneath it rather than everything being redone.

## Running it

```bash
python3 format_srt.py    raw.srt  formatted.srt --songs 90-140,600-700
python3 fix_pt.py        formatted.srt  fixed.srt
python3 check_grammar.py fixed.srt  checked.srt          # or --report
python3 retime.py        film.mkv -o word_times.json     # word-level timings
python3 apply_times.py   checked.srt  word_times.json  final.srt
python3 fix_timing.py    final.srt  final.srt            # optional second pass
```

`--songs` takes second ranges that are sung. Without it nothing is marked as
song, which is the safe default.

## Films

No film, and no film's subtitles, live in this repo. Subtitles are a derivative
work of the film they came from, so they stay with whoever holds the film. The
tool is the part that can be shared.

*Beauty and the Beast* was the first film through it, and is where the
Brazilian→European word list and the phrase fixes below came from.

## Licence

MIT — see `LICENSE`.

## Known rough edges

- `format_srt.py`, `fix_pt.py`, `check_grammar.py` and `fix_timing.py` still
  need chaining by hand. One entry point that runs all six in order is the
  obvious next step.
- The Brazilian→European word list in `fix_pt.py` and the phrase fixes in
  `check_grammar.py` are hand-built from what one film happened to contain.
  They will grow with each new one, which argues for moving them out of the
  code and into a data file.
- Song ranges are passed by hand. Whisper knows where the music is; nothing
  currently asks it.
