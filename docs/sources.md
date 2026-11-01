# Feed sources and use notes

The application reads only the public RSS/Atom endpoints below. It does not crawl article pages. The feed endpoints responded successfully during the initial implementation check on 2026-11-01, but publishers can change or restrict them at any time.

| Publisher / feed | Feed endpoint | Attribution / coverage |
|---|---|---|
| BBC News — World | [RSS](https://feeds.bbci.co.uk/news/world/rss.xml) | [BBC News](https://www.bbc.com/news), global English headlines |
| BBC News — Amharic | [RSS](https://feeds.bbci.co.uk/amharic/rss.xml) | [BBC News Amharic](https://www.bbc.com/amharic), Amharic-language coverage |
| The Reporter Ethiopia | [RSS](https://www.thereporterethiopia.com/feed/) | [The Reporter Ethiopia](https://www.thereporterethiopia.com/), Ethiopia-focused English coverage |
| Al Jazeera | [RSS](https://www.aljazeera.com/xml/rss/all.xml) | [Al Jazeera](https://www.aljazeera.com/), global English coverage |

BBC's [news feed guidance](https://www.bbc.co.uk/news/10628494) asks sites displaying BBC feed content to use proper attribution and links to its [RSS terms](https://www.bbc.co.uk/terms/additional_rss.shtml). Public feed availability does not mean that article text or summaries are freely licensed for republication. Before public hosting, review each publisher's current terms, retain attribution, link users to the original story, and remove a feed on request or if its terms prohibit the use.

This starter stores only RSS-provided title, URL, source, timestamp, feed category and short description. No article-body scraping, private feed, login, or paywall bypass is used. The app makes requests sequentially, with a timeout and a 5 MB response cap.

## Refresh and removal

Feed URLs live in `config/feeds.json`. Remove or amend a source there if it becomes unavailable or its policy changes. Runtime cache files are local under `data/`, are not committed, and can be cleared by deleting that directory.
