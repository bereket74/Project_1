# Evaluation and verification

## What works

- **Offline tests:** 18 tests passed on Python 3.12.3. Ruff and `compileall` passed, and a fresh `pip wheel --no-deps` built the project package.
- **Live feed check:** on 2026-11-01, the configured four RSS feeds returned 93 items with zero feed warnings: BBC News — World (25), BBC News — Amharic (33), The Reporter Ethiopia (10), and Al Jazeera — All (25).
- **Synthetic mode:** locally, with `SPACE_ID` set, the app returned seven fictional examples with no story URLs and did not enter the live-feed pipeline. The local environment lacked the Space-only model package, so the GPU button remained hidden as designed.
- **GPU search code path:** deterministic fake-model tests verify E5 `query:`/`passage:` prefixes, relevant ranking, and that the callback uses only the loaded synthetic examples without calling the feed pipeline. This is code-path testing, not a benchmark of the real model.
- **Model/dependency checks:** the pinned E5 revision is public and lists an MIT license; package metadata resolves for Python 3.10+, and the model weights were not downloaded in local tests.

The live snapshot contained 33 unclassified items from the Amharic feed; sentiment was explicitly unsupported for those items. Among the other 60 items, the VADER labels were 39 negative, 17 positive, and 4 neutral. The TF-IDF grouper found zero clusters in the live snapshot. These are operational counts, not measures of model quality.

## Hosted runtime status

The public Space source is [klohdfhk/ai-news-intelligence](https://huggingface.co/spaces/klohdfhk/ai-news-intelligence). Its previously uploaded CPU-only version returned `RUNTIME_ERROR` because ZeroGPU detected no decorated handler. The local source now has a real `@spaces.GPU(duration=30)` callback, pinned multilingual E5 model loaded on CUDA at startup, and the exact Space dependency set. The updated public build and one live GPU inference check are still pending; no hosted model inference is claimed yet.

## What is not measured

There is no licensed, labeled benchmark in this project. Topic, sentiment, entity extraction, grouping, search, and trend quality metrics are therefore not reported. The TF-IDF clustering test uses synthetic near-duplicates and does not establish real-world grouping accuracy. Trend counts use only the feed items presently returned; they are descriptive, not comprehensive or predictive. Amharic semantic-search relevance has not been benchmarked.

Live excerpts remain for local exploration only. The public Space contains only synthetic-demo code and examples; no publisher stories or feed data were uploaded. Publisher-use notes and links are in [`sources.md`](sources.md).
