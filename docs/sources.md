# Feed sources and use notes

The application reads only the public RSS/Atom endpoints below. It does not crawl article pages. The feed endpoints responded successfully during the initial implementation check on 2026-11-01, but publishers can change or restrict them at any time.

| Publisher / feed | Feed endpoint | Attribution / coverage |
|---|---|---|
| BBC News — World | [RSS](https://feeds.bbci.co.uk/news/world/rss.xml) | [BBC News](https://www.bbc.com/news), global English headlines |
| BBC News — Amharic | [RSS](https://feeds.bbci.co.uk/amharic/rss.xml) | [BBC News Amharic](https://www.bbc.com/amharic), Amharic-language coverage |
| The Reporter Ethiopia | [RSS](https://www.thereporterethiopia.com/feed/) | [The Reporter Ethiopia](https://www.thereporterethiopia.com/), Ethiopia-focused English coverage |
| Al Jazeera | [RSS](https://www.aljazeera.com/xml/rss/all.xml) | [Al Jazeera](https://www.aljazeera.com/), global English coverage |

The BBC's [feed guidance](https://www.bbc.com/news/help-11144227) says the feeds are available for personal and non-commercial use and specifies BBC News/website attribution when feed content appears. It links to [additional RSS terms](https://www.bbc.co.uk/terms/additional_rss.shtml). Al Jazeera's [terms and conditions](https://www.aljazeera.com/terms-and-conditions) describe its content as for personal, non-commercial use and restrict copying or distribution without express prior written permission. I did not find clear feed-reuse permission for The Reporter Ethiopia's RSS endpoint. These pages are guidance, not a legal determination of whether any particular portfolio demo is permitted.

**Hosting decision:** the live-feed mode is for local exploration with attribution and links; it is not being published while reuse rights are unclear. The app switches to clearly labeled, fictional examples whenever `SPACE_ID` is present, a built-in variable listed in the [official Spaces runtime documentation](https://huggingface.co/docs/hub/spaces-overview). Any public Space must remain in that synthetic-only mode and make no live RSS requests. The repository contains only code and source URLs, not publisher stories or a feed dataset. This is a conservative project decision, not legal advice.

This starter stores only RSS-provided title, URL, source, timestamp, feed category and short description locally. No article-body scraping, private feed, login, or paywall bypass is used. The app makes requests sequentially, with a timeout and a 5 MB response cap.

## Refresh and removal

Feed URLs live in `config/feeds.json`. Remove or amend a source there if it becomes unavailable or its policy changes. Runtime cache files are local under `data/`, are not committed, and can be cleared by deleting that directory.

## Semantic search model and GPU runtime

The Space's explicit multilingual search button uses [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small), pinned to model revision `614241f622f53c4eeff9890bdc4f31cfecc418b3`. The model card lists an MIT license and support for 100 languages, requires `query: ` and `passage: ` prefixes for retrieval, and warns that low-resource languages may see degraded performance. Its performance for Amharic is not benchmarked in this project.

The [ZeroGPU documentation](https://huggingface.co/docs/hub/spaces-zerogpu) requires GPU-dependent functions to use `@spaces.GPU`; models should be placed on CUDA at module startup, and a short duration improves queue priority. The app uses the default `large` size and a 30-second cap. GPU inference is available only through the explicit button; page load, feed safety, and ordinary filters remain CPU-only. ZeroGPU calls may consume the caller's included daily quota.
