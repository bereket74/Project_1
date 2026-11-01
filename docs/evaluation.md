# Evaluation and smoke-check notes

## Offline tests

The first full test run completed with **11 passing tests** on Python 3.12.3 using the pinned project environment. Coverage includes feed parsing and canonicalization, unsupported schemes, English topic/sentiment baselines, Amharic guardrails, bounded extractive briefs, TF-IDF duplicate grouping, empty-vocabulary handling, local cache schema, UI filtering, and HTML/URL escaping.

The duplicate-story test uses a clearly synthetic fixture. It verifies code behavior only; it is not an estimate of real-world precision or recall.

## Live feed smoke check

On 2026-11-01, the collector fetched and analyzed 46 items using a per-feed limit of 12. All four configured endpoints returned usable items with **0 feed warnings** in that run:

| Source | Items |
|---|---:|
| BBC News — World | 12 |
| BBC News — Amharic | 12 |
| The Reporter Ethiopia | 10 |
| Al Jazeera — All | 12 |

Analysis output in that sample: 15 politics, 2 conflict, 1 business, 1 technology, 1 sports, 6 world, 8 general and 12 unclassified (Amharic); 24 negative, 9 positive, 1 neutral and 12 unsupported sentiment labels. The results are descriptive counts from a small live snapshot, not accuracy measurements. VADER sentiment is especially sensitive to short headlines and feed snippets.

The lexical TF-IDF grouper found **no related-story clusters** in this 46-item snapshot at its configured threshold. The offline synthetic test confirms it can group near-duplicate items, but this live result shows the baseline has not yet demonstrated useful cross-publisher grouping. Next improvement: assess several snapshots against a manually reviewed, licensed duplicate-story set and tune/report precision and recall before making quality claims.

## What is not evaluated yet

There is no labeled, licensed dataset in this starter, so topic, sentiment, NER, and clustering quality metrics are intentionally not reported. In particular, the keyword topic baseline, VADER English sentiment, capitalization fallback, and Amharic unsupported label are not interchangeable with validated language models. The output is for exploration, not editorial, public-safety, or financial decisions.
