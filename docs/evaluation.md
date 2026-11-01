# Evaluation and smoke-check notes

## Offline tests

The final full test run completed with **15 passing tests** on Python 3.12.3 using the project virtual environment. Coverage includes feed parsing and canonicalization, unsupported schemes, English topic/sentiment baselines, Amharic guardrails, bounded extractive briefs, TF-IDF duplicate grouping, empty-vocabulary handling, local cache schema, UI filtering and HTML/URL escaping, similarity ranking, and trend-window arithmetic.

The duplicate-story test uses a clearly synthetic fixture. It verifies code behavior only; it is not an estimate of real-world precision or recall.

## Live feed smoke check

On 2026-11-01, the collector fetched and analyzed **93 items** using a per-feed limit of 35. All four configured endpoints returned usable items with **0 feed warnings** in that run:

| Source | Items |
|---|---:|
| BBC News — World | 25 |
| BBC News — Amharic | 33 |
| The Reporter Ethiopia | 10 |
| Al Jazeera — All | 25 |

Analysis output in that sample: 21 politics, 6 conflict, 1 business, 2 technology, 1 sports, 1 climate, 7 world, 21 general, and 33 unclassified items (the Amharic feed); 39 negative, 17 positive, 4 neutral, and 33 unsupported sentiment labels. These are descriptive counts from one live snapshot, not accuracy measurements. Amharic sentiment is explicitly unsupported, and English VADER output is sensitive to short headlines and feed snippets.

The lexical TF-IDF grouper found **no related-story clusters** in this 93-item snapshot at its configured threshold. The offline synthetic test confirms it can group near-duplicate items, but this live result shows that useful real-world cross-publisher grouping has not yet been demonstrated. The next improvement is a manually reviewed, licensed duplicate-story set followed by precision/recall evaluation before changing the threshold or making quality claims. The local Gradio page also returned HTTP 200; this checks startup and page serving, not deployment or every interaction.

## What is not evaluated yet

There is no labeled, licensed dataset in this starter, so topic, sentiment, NER, clustering, search, and trend-quality metrics are intentionally not reported. In particular, the keyword topic baseline, VADER English sentiment, capitalization fallback, TF-IDF retrieval, and Amharic unsupported label are not interchangeable with validated language models. Trend changes are descriptive, not forecasts. The output is for exploration, not editorial, public-safety, or financial decisions.


## Interactive callback

A fresh Gradio client invocation of the UI's `refresh_news` callback returned rendered story cards and a success message for **93 items across the four configured feeds**. This is a separate, larger fetch than the 46-item CLI snapshot above; feed contents and counts naturally change. The UI endpoint health check also returned HTTP 200 with the expected application title. Neither check evaluates model accuracy.

The topic pulse uses only currently returned feed items; it does not maintain a complete historical archive. Treat window comparisons as a small, potentially incomplete feed sample.
