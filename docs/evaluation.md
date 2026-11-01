# Evaluation and verification

## What works

- **Offline tests:** 16 tests passed on Python 3.12.3. Ruff and `compileall` passed, and `pip wheel --no-deps` built the project wheel.
- **Live feed check:** on 2026-11-01, the configured four RSS feeds returned 93 items with zero feed warnings: BBC News — World (25), BBC News — Amharic (33), The Reporter Ethiopia (10), and Al Jazeera — All (25).
- **Synthetic mode:** locally, with `SPACE_ID` set, the app returned seven fictional examples, omitted story links, displayed the synthetic refresh control, and bypassed the live RSS pipeline. The public Space source is [klohdfhk/ai-news-intelligence](https://huggingface.co/spaces/klohdfhk/ai-news-intelligence), but its hosted runtime is `RUNTIME_ERROR`: ZeroGPU reported `No @spaces.GPU function detected during startup`.

The live snapshot contained 33 unclassified items from the Amharic feed; sentiment was explicitly unsupported for those items. Among the other 60 items, the VADER labels were 39 negative, 17 positive, and 4 neutral. The TF-IDF grouper found zero clusters in the live snapshot. These are operational counts, not measures of model quality.

## What is not measured

There is no licensed, labeled benchmark in this project. Topic, sentiment, entity extraction, grouping, search, and trend quality metrics are therefore not reported. The TF-IDF clustering test uses synthetic near-duplicates and does not establish real-world grouping accuracy. Trend counts use only the feed items presently returned; they are descriptive, not comprehensive or predictive.

Live excerpts remain for local exploration only. The public Space repository contains only the synthetic-demo code and examples; no publisher stories or feed data were uploaded. Its source is public, but the interactive runtime is not currently serving. Publisher-use notes and links are in [`sources.md`](sources.md).
