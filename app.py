from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any

import gradio as gr

from newsintel.pipeline import run_intelligence
from newsintel.discovery import NewsSearch, topic_trends
from newsintel.rss import canonicalize_url, load_sources
from newsintel.storage import load_cache, save_cache

ROOT = Path(__file__).resolve().parent
FEEDS_PATH = ROOT / "config" / "feeds.json"
CACHE_PATH = ROOT / "data" / "latest_articles.json"
SEARCH = NewsSearch()


def _matches(article: dict[str, Any], topic: str, mood: str, query: str, ethiopia_only: bool) -> bool:
    if topic != "All topics" and article.get("topic") != topic:
        return False
    if mood != "All sentiment" and article.get("sentiment") != mood.lower():
        return False
    if ethiopia_only and article.get("region") != "ethiopia":
        return False
    needle = query.casefold().strip()
    if needle:
        searchable = " ".join([
            str(article.get("title", "")), str(article.get("summary", "")),
            str(article.get("source", "")), str(article.get("topic", "")),
            " ".join(str(entity.get("text", "")) for entity in article.get("entities", [])),
        ]).casefold()
        if needle not in searchable:
            return False
    return True


def render_cards(articles: list[dict[str, Any]]) -> str:
    if not articles:
        return '<div class="empty">No stories match these filters. Refresh feeds or broaden your search.</div>'
    cards: list[str] = []
    for article in articles[:60]:
        title = html.escape(str(article.get("title", "Untitled")))
        url = html.escape(canonicalize_url(str(article.get("url", ""))) or "#", quote=True)
        source = html.escape(str(article.get("attribution", article.get("source", "Source"))))
        published = html.escape(str(article.get("published", "Date unavailable")))
        summary = html.escape(str(article.get("brief_summary", article.get("summary", ""))))
        topic = html.escape(str(article.get("topic", "general")))
        mood = html.escape(str(article.get("sentiment", "unsupported")))
        cluster = article.get("cluster_id")
        cluster_size = int(article.get("cluster_size", 1))
        group = f'<span class="tag">Related coverage: {cluster_size}</span>' if cluster else ""
        entity_names = [str(e.get("text", "")) for e in article.get("entities", [])[:5]]
        entities = ", ".join(html.escape(name) for name in entity_names)
        entity_line = f'<div class="entities">Entities: {entities}</div>' if entities else ""
        cards.append(
            '<article class="story">'
            f'<div class="meta"><span>{source}</span><span>{published}</span></div>'
            f'<h3><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></h3>'
            f'<p>{summary}</p>'
            f'<div class="tags"><span class="tag">{topic}</span><span class="tag sentiment">{mood}</span>{group}</div>'
            f'{entity_line}'
            '</article>'
        )
    return '<div class="stories">' + "".join(cards) + "</div>"


def render_trends(articles: list[dict[str, Any]]) -> str:
    trends = topic_trends(articles)
    if not trends:
        return "### Topic pulse\nNo current-window topics yet. Refresh feeds to build a trend baseline."
    lines = ["### Topic pulse — last 7 days vs. previous 7 days"]
    for row in trends[:8]:
        change = row["change_pct"]
        delta = "new" if row["previous_count"] == 0 else f"{change:+.1f}%"
        lines.append(f"- **{html.escape(str(row['topic']))}** — {row['current_count']} items; {delta} vs. prior window")
    lines.append("\nCounts reflect feed publication timestamps; they are descriptive, not forecasts.")
    return "\n".join(lines)


def refresh_news() -> tuple[list[dict[str, Any]], str, str, str]:
    try:
        sources = load_sources(FEEDS_PATH)
        articles, errors = run_intelligence(sources, timeout=12.0, per_feed_limit=80)
        if articles:
            save_cache(CACHE_PATH, articles)
            note = f"Fetched and analyzed {len(articles)} RSS items from {len(sources)} configured feeds."
            if errors:
                note += " Some feeds were unavailable: " + "; ".join(errors)
            return articles, render_cards(articles), note, render_trends(articles)
        cached = load_cache(CACHE_PATH)
        if cached:
            return cached, render_cards(cached), "No live feed returned items. Showing the last saved cache. " + "; ".join(errors), render_trends(cached)
        return [], render_cards([]), "No feed items were returned. " + "; ".join(errors), render_trends([])
    except Exception as exc:
        try:
            cached = load_cache(CACHE_PATH)
        except Exception:
            cached = []
        if cached:
            return cached, render_cards(cached), f"Refresh failed ({type(exc).__name__}). Showing local cache.", render_trends(cached)
        return [], render_cards([]), f"Refresh failed ({type(exc).__name__}: {exc}). Try again later.", render_trends([])


def apply_filters(articles: list[dict[str, Any]], topic: str, mood: str,
                  query: str, ethiopia_only: bool, search_mode: str = "Contains") -> tuple[str, str]:
    similarity = search_mode == "Similarity (TF-IDF)" and bool(query.strip())
    filtered = [a for a in articles if _matches(a, topic, mood, "" if similarity else query, ethiopia_only)]
    if similarity:
        ranked = SEARCH.rank(query, filtered, limit=60)
        filtered = [article for article, _score in ranked]
        note = f"Showing {len(filtered)} of {len(articles)} analyzed stories. Search: {SEARCH.backend}."
        if SEARCH.warning:
            note += " " + SEARCH.warning
    else:
        note = f"Showing {len(filtered)} of {len(articles)} analyzed stories."
    return render_cards(filtered), note


CSS = """
.gradio-container {max-width: 1120px !important; margin: auto !important;}
.story {border: 1px solid #dce3ed; border-radius: 14px; padding: 18px 20px; margin: 14px 0; background: white;}
.story h3 {font-size: 1.12rem; line-height: 1.45; margin: 10px 0;}
.story a {color: #183a67; text-decoration: none;}
.story a:hover {text-decoration: underline;}
.story p {color: #3d4755; line-height: 1.6; margin: 8px 0 12px;}
.meta {display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; color:#687588; font-size:.84rem;}
.tags {display:flex; gap:7px; flex-wrap:wrap;}
.tag {background:#eef3fa; color:#315176; padding:4px 9px; border-radius:999px; font-size:.78rem;}
.sentiment {background:#f4f1ea; color:#705a2b;}
.entities {margin-top:10px; color:#687588; font-size:.82rem;}
.empty {padding:28px; border:1px dashed #aab6c6; border-radius:12px; color:#586779;}
"""

with gr.Blocks(title="AI News Intelligence", theme=gr.themes.Soft(), css=CSS) as demo:
    gr.Markdown("# AI News Intelligence\nA source-linked news desk built on public RSS feeds. Analyses are lightweight and inspectable; Amharic sentiment/NER are intentionally marked unsupported until validated.")
    with gr.Row():
        refresh_button = gr.Button("Refresh public feeds", variant="primary")
        status = gr.Markdown("Loading news feeds…")
    articles_state = gr.State([])
    with gr.Row():
        topic_filter = gr.Dropdown(["All topics", "politics", "business", "technology", "health", "climate", "science", "sports", "conflict", "world", "general"], value="All topics", label="Topic")
        sentiment_filter = gr.Dropdown(["All sentiment", "Positive", "Neutral", "Negative", "Unsupported"], value="All sentiment", label="Sentiment")
        search_box = gr.Textbox(label="Search stories", placeholder="Headline, source, entity, or snippet")
        search_mode = gr.Dropdown(["Contains", "Similarity (TF-IDF)"], value="Contains", label="Search mode")
        ethiopia_filter = gr.Checkbox(label="Ethiopia-focused sources", value=False)
    topic_pulse = gr.Markdown(render_trends([]))
    stories = gr.HTML(render_cards([]))
    refresh_button.click(refresh_news, outputs=[articles_state, stories, status, topic_pulse])
    for component in (topic_filter, sentiment_filter, search_box, search_mode, ethiopia_filter):
        component.change(apply_filters, inputs=[articles_state, topic_filter, sentiment_filter, search_box, ethiopia_filter, search_mode], outputs=[stories, status])
    demo.load(refresh_news, outputs=[articles_state, stories, status, topic_pulse])

if __name__ == "__main__":
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        show_error=True,
    )
