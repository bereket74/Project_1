# Evaluation and verification

## What works

- **Offline tests:** 16 tests passed on Python 3.12.3. Ruff and `compileall` passed, and `pip wheel --no-deps` built the project wheel.
- **Live feed check:** on 2026-11-01, the configured four RSS feeds returned 93 items with zero feed warnings: BBC News — World (25), BBC News — Amharic (33), The Reporter Ethiopia (10), and Al Jazeera — All (25).
- **Synthetic Space path:** with `SPACE_ID` set, the app returned seven fictional examples, omitted story links, used the “Refresh synthetic examples” control, and did not call the live RSS pipeline. The local Space-mode page returned HTTP 200. No public Hugging Face Space has been published.

The live snapshot contained 33 unclassified items from the Amharic feed; sentiment was explicitly unsupported for those items. Among the other 60 items, the VADER labels were 39 negative, 17 positive, and 4 neutral. The TF-IDF grouper found zero clusters in the live snapshot. These are operational counts, not measures of model quality.

## What is not measured

There is no licensed, labeled benchmark in this project. Topic, sentiment, entity extraction, grouping, search, and trend quality metrics are therefore not reported. The TF-IDF clustering test uses synthetic near-duplicates and does not establish real-world grouping accuracy. Trend counts use only the feed items presently returned; they are descriptive, not comprehensive or predictive.

Live excerpts remain for local exploration only. The synthetic Space mode avoids redistributing those excerpts, but a public Space has not yet been created. Publisher-use notes and links are in [`sources.md`](sources.md).