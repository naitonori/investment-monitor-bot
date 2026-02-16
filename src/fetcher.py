"""
News Fetcher Module - The Immortal Collector
ネットワークエラーがあっても絶対に停止しない
"""
import feedparser
import requests
from typing import List, Dict, Set
from pathlib import Path
from loguru import logger
from config import config


class NewsFetcher:
    """Crash-resistant news fetcher with duplicate filtering and keyword categorization"""

    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.last_seen_file = Path(config.LAST_SEEN_FILE)
        self._load_last_seen()

    def _load_last_seen(self):
        try:
            if self.last_seen_file.exists():
                with open(self.last_seen_file, "r", encoding="utf-8") as f:
                    for line in f:
                        url = line.strip()
                        if url:
                            self.seen_urls.add(url)
                logger.info(f"Loaded {len(self.seen_urls)} previously seen URLs")
        except Exception as e:
            logger.warning(f"Failed to load last_seen.txt: {e}")

    def _save_url(self, url: str):
        try:
            with open(self.last_seen_file, "a", encoding="utf-8") as f:
                f.write(f"{url}\n")
        except Exception as e:
            logger.warning(f"Failed to save URL: {e}")

    def _trim_seen_file(self):
        """Keep only the last 500 URLs to prevent file bloat"""
        try:
            if not self.last_seen_file.exists():
                return
            lines = self.last_seen_file.read_text(encoding="utf-8").strip().split("\n")
            if len(lines) > 500:
                trimmed = lines[-500:]
                self.last_seen_file.write_text(
                    "\n".join(trimmed) + "\n", encoding="utf-8"
                )
                self.seen_urls = {u.strip() for u in trimmed if u.strip()}
                logger.info(f"Trimmed seen URLs to {len(self.seen_urls)}")
        except Exception as e:
            logger.warning(f"Failed to trim seen file: {e}")

    def fetch_all_news(self) -> List[Dict[str, str]]:
        """Fetch news from all RSS feeds"""
        all_news = []

        for feed_url in config.RSS_FEEDS:
            try:
                items = self._fetch_single_feed(feed_url)
                all_news.extend(items)
                logger.success(f"Fetched {len(items)} items from {feed_url[:50]}...")
            except Exception as e:
                logger.error(f"Failed to fetch {feed_url[:50]}...: {e}")
                continue

        # Periodic cleanup
        self._trim_seen_file()

        return all_news

    def _fetch_single_feed(self, feed_url: str) -> List[Dict[str, str]]:
        news_items = []

        response = requests.get(
            feed_url,
            timeout=config.HTTP_TIMEOUT,
            headers={"User-Agent": "InvestmentMonitorBot/2.0"},
        )
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        if feed.bozo:
            logger.warning(f"RSS parse warning: {feed.bozo_exception}")

        for entry in feed.entries[:30]:
            try:
                url = entry.get("link", "")
                if not url or url in self.seen_urls:
                    continue

                title = entry.get("title", "No title")
                summary = entry.get("summary", entry.get("description", ""))
                published = entry.get("published", entry.get("updated", ""))

                # Keyword matching with category detection
                matched_keywords = self._find_matched_keywords(title, summary)
                if not matched_keywords:
                    continue

                # Determine category from matched keywords
                category = config.classify_keyword(
                    " ".join(matched_keywords)
                )

                news_items.append({
                    "title": title,
                    "link": url,
                    "published": published,
                    "summary": summary[:500],
                    "matched_keywords": ", ".join(matched_keywords),
                    "category": category,
                })

                self.seen_urls.add(url)
                self._save_url(url)

            except Exception as e:
                logger.warning(f"Failed to parse entry: {e}")
                continue

        return news_items

    def _find_matched_keywords(self, title: str, summary: str) -> List[str]:
        """Return list of keywords that matched in the text"""
        if not config.ALL_KEYWORDS:
            return ["all"]

        text = f"{title} {summary}".lower()
        matched = []
        for kw in config.ALL_KEYWORDS:
            if kw.lower() in text:
                matched.append(kw)
        return matched
