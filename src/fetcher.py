"""
News Fetcher Module - The Immortal Collector
RSSからニュースを取得し、記事本文まで読み込む
"""
import re
import feedparser
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Set
from pathlib import Path
from datetime import datetime, timezone, timedelta
from time import mktime
from loguru import logger
from config import config


class NewsFetcher:
    """Crash-resistant news fetcher with article body extraction"""

    def __init__(self):
        self.seen_urls: Set[str] = set()
        self.seen_titles: Set[str] = set()
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

                # === 24時間以内のニュースのみ通す ===
                if not self._is_recent(entry):
                    continue

                title = entry.get("title", "No title")

                # === 類似タイトルの重複スキップ ===
                if self._is_duplicate_title(title):
                    continue

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

                # === 記事本文を取得 ===
                article_body = self._fetch_article_body(url)

                news_items.append({
                    "title": title,
                    "link": url,
                    "published": published,
                    "summary": summary[:500],
                    "article_body": article_body,
                    "matched_keywords": ", ".join(matched_keywords),
                    "category": category,
                })

                self.seen_urls.add(url)
                self._save_url(url)

            except Exception as e:
                logger.warning(f"Failed to parse entry: {e}")
                continue

        return news_items

    def _fetch_article_body(self, url: str) -> str:
        """
        記事のURLにアクセスして本文テキストを抽出する
        失敗しても空文字を返す（絶対にクラッシュしない）
        """
        try:
            response = requests.get(
                url,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                },
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # 不要なタグを削除
            for tag in soup.find_all(["script", "style", "nav", "header",
                                       "footer", "aside", "iframe", "form"]):
                tag.decompose()

            # 記事本文を抽出（優先度順に検索）
            article_text = ""

            # 方法1: <article> タグ
            article_tag = soup.find("article")
            if article_tag:
                article_text = article_tag.get_text(separator="\n", strip=True)

            # 方法2: よくある記事クラス名
            if not article_text:
                for selector in [
                    ".article-body", ".article_body", ".articleBody",
                    ".entry-content", ".post-content", ".news-body",
                    ".story-body", "#article-body", ".main-content",
                    ".newsDetail", ".content-main",
                ]:
                    elem = soup.select_one(selector)
                    if elem:
                        article_text = elem.get_text(separator="\n", strip=True)
                        break

            # 方法3: <p> タグを全て取得
            if not article_text:
                paragraphs = soup.find_all("p")
                texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20]
                article_text = "\n".join(texts)

            # 最大2000文字に制限（API コスト節約）
            if article_text:
                article_text = article_text[:2000]
                logger.info(f"Article body extracted: {len(article_text)} chars")
            else:
                logger.info(f"No article body found for: {url[:50]}")

            return article_text

        except requests.Timeout:
            logger.warning(f"Timeout fetching article: {url[:50]}")
            return ""
        except Exception as e:
            logger.warning(f"Failed to fetch article body: {e}")
            return ""

    def _normalize_title(self, title: str) -> str:
        """タイトルを正規化して比較用のキーを作る"""
        # ソース名を除去: 「〜 - ロイター」「〜(共同通信)」「〜 | Bloomberg」
        t = re.sub(r'\s*[-|｜]\s*[^-|｜]+$', '', title)
        t = re.sub(r'\s*[（(][^）)]+[）)]\s*$', '', t)
        # 空白・記号を除去して小文字化
        t = re.sub(r'[\s　、。・！？!?,.\-:：【】「」『』\u3000]+', '', t)
        return t.lower()[:40]

    def _is_duplicate_title(self, title: str) -> bool:
        """類似タイトルが既に処理済みかチェック"""
        normalized = self._normalize_title(title)
        if not normalized:
            return False
        if normalized in self.seen_titles:
            logger.info(f"Duplicate skipped: {title[:50]}...")
            return True
        self.seen_titles.add(normalized)
        return False

    def _is_recent(self, entry) -> bool:
        """24時間以内のニュースかどうかを判定する"""
        try:
            # feedparser が解析した日時構造体を使う
            published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
            if not published_parsed:
                # 日時情報がない場合は通す（新着として扱う）
                return True

            entry_time = datetime.fromtimestamp(mktime(published_parsed), tz=timezone.utc)
            now = datetime.now(timezone.utc)
            age = now - entry_time

            if age > timedelta(hours=24):
                return False
            return True
        except Exception:
            # パースに失敗したら通す（安全側に倒す）
            return True

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
