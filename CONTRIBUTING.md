# Contributing

1. Create a virtual environment and install `requirements.txt`.
2. Run `pytest` before and after changes.
3. Keep feed ingestion limited to public RSS/Atom endpoints. Do not add article-page scraping or feeds that require credentials.
4. Preserve publisher attribution, canonical article links, and the language guardrails.
5. Never call rule scores calibrated confidence or report model quality without a labeled evaluation set.
6. Add offline fixtures for parsing behavior; label synthetic fixtures clearly and keep them free of real copyrighted article text.
7. Document source policy changes in `docs/sources.md`.

Open an issue for proposed new analysis methods, including the data and validation plan needed to evaluate them.
