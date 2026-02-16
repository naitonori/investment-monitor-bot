"""
Configuration Module - Dual Keyword Strategy
保有株防衛 + 新規チャンス発掘の二刀流設定
"""
import os
from typing import List, Dict
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


class Config:
    """Crash-resistant configuration with dual keyword strategy"""

    def __init__(self):
        # === API Keys ===
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

        # === Monitoring Settings ===
        self.INTERVAL_SECONDS = self._safe_int("INTERVAL_SECONDS", 60)
        self.CLAUDE_TIMEOUT = self._safe_int("CLAUDE_TIMEOUT", 30)
        self.HTTP_TIMEOUT = self._safe_int("HTTP_TIMEOUT", 15)

        # === 1. 保有株リスト（防御・買い増し） ===
        my_stocks_str = os.getenv("MY_STOCKS",
            "東京応化,4186,フォトレジスト,"
            "三菱重工,7011,川崎重工,7012,防衛省,防衛費")
        self.MY_PORTFOLIO: List[str] = [
            k.strip() for k in my_stocks_str.split(",") if k.strip()
        ]

        # === 2. 新規チャンス発掘リスト（攻撃） ===
        opportunity_str = os.getenv("OPPORTUNITY_KEYWORDS",
            "上方修正,最高益,増配,自社株買い,ストップ高,"
            "業務提携,資本提携,買収,TOB,MBO,"
            "世界初,画期的,AI半導体,データセンター")
        self.OPPORTUNITY_KEYWORDS: List[str] = [
            k.strip() for k in opportunity_str.split(",") if k.strip()
        ]

        # === 全キーワード結合 ===
        self.ALL_KEYWORDS: List[str] = self.MY_PORTFOLIO + self.OPPORTUNITY_KEYWORDS

        # === キーワードカテゴリマップ ===
        self.KEYWORD_CATEGORIES: Dict[str, str] = {}
        for kw in self.MY_PORTFOLIO:
            self.KEYWORD_CATEGORIES[kw.lower()] = "portfolio"
        for kw in self.OPPORTUNITY_KEYWORDS:
            self.KEYWORD_CATEGORIES[kw.lower()] = "opportunity"

        # === RSS Feeds (日本株向け) ===
        self.RSS_FEEDS: List[str] = self._load_rss_feeds()

        # === Claude Model ===
        self.CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")

        # === State File ===
        self.LAST_SEEN_FILE = os.getenv("LAST_SEEN_FILE", "last_seen.txt")

        self._validate()

    def _load_rss_feeds(self) -> List[str]:
        """Load RSS feeds from env or use defaults"""
        custom_feeds = os.getenv("RSS_FEEDS")
        if custom_feeds:
            return [f.strip() for f in custom_feeds.split(",") if f.strip()]

        return [
            # Yahoo!ファイナンス 株式ニュース
            "https://finance.yahoo.co.jp/rss/news?category=stock",
            # 日経（Google News経由）
            "https://news.google.com/rss/search?q=%E6%A0%AA%E5%BC%8F+%E6%B1%BA%E7%AE%97&hl=ja&gl=JP&ceid=JP:ja",
            # ロイター ビジネス
            "https://news.google.com/rss/search?q=%E6%97%A5%E6%9C%AC%E6%A0%AA+%E6%9D%90%E6%96%99&hl=ja&gl=JP&ceid=JP:ja",
        ]

    def _safe_int(self, key: str, default: int) -> int:
        try:
            value = os.getenv(key)
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            logger.warning(f"Invalid integer for {key}, using default: {default}")
            return default

    def _validate(self):
        errors = []
        if not self.ANTHROPIC_API_KEY:
            errors.append("ANTHROPIC_API_KEY is not set")
        if not self.DISCORD_WEBHOOK_URL:
            errors.append("DISCORD_WEBHOOK_URL is not set")
        if errors:
            for e in errors:
                logger.error(f"  - {e}")
            logger.warning("Bot will start but some features may not work")

    def classify_keyword(self, text: str) -> str:
        """Classify matched text as 'portfolio' or 'opportunity'"""
        text_lower = text.lower()
        for kw in self.MY_PORTFOLIO:
            if kw.lower() in text_lower:
                return "portfolio"
        for kw in self.OPPORTUNITY_KEYWORDS:
            if kw.lower() in text_lower:
                return "opportunity"
        return "unknown"

    def __repr__(self):
        return (
            f"Config(interval={self.INTERVAL_SECONDS}s, "
            f"portfolio={len(self.MY_PORTFOLIO)} keywords, "
            f"opportunity={len(self.OPPORTUNITY_KEYWORDS)} keywords, "
            f"feeds={len(self.RSS_FEEDS)}, "
            f"api_key={'SET' if self.ANTHROPIC_API_KEY else 'NOT SET'}, "
            f"webhook={'SET' if self.DISCORD_WEBHOOK_URL else 'NOT SET'})"
        )


config = Config()
