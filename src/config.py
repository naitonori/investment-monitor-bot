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

        # === 保有銘柄（AI分析に渡す用） ===
        self.HOLDINGS = [
            {"name": "川崎重工業", "code": "7012"},
            {"name": "東京応化工業", "code": "4186"},
            {"name": "三菱重工業", "code": "7011"},
        ]

        # === 1. 保有株リスト（防御・買い増し） ===
        # 東京応化工業 (4186): AI・半導体・微細化
        # + グローバル半導体サプライチェーン連想キーワード
        tokyo_ohka = [
            "東京応化", "4186",
            "EUV", "極端紫外線",
            "フォトレジスト", "感光材",
            "TSMC", "熊本工場", "JASM",
            "ラピダス", "2ナノ", "微細化",
            "HBM", "広帯域メモリ",
            "パッケージング", "3次元実装",
            "SOX指数", "フィラデルフィア半導体",
            # === グローバル半導体（連想分析用） ===
            "NVIDIA", "エヌビディア", "Jensen Huang",
            "Intel", "インテル", "Pat Gelsinger",
            "AMD", "リサ・スー", "Lisa Su",
            "Qualcomm", "クアルコム",
            "ASML", "EUV装置",
            "Samsung", "サムスン半導体",
            "Micron", "マイクロン",
            "SK hynix", "SKハイニックス",
            "Applied Materials", "東京エレクトロン", "8035",
            "半導体製造装置", "ウェハ",
            "AI半導体", "GPU", "データセンター",
            "生成AI", "ChatGPT", "LLM", "OpenAI",
            "CoWoS", "先端パッケージ",
            "半導体規制", "対中規制", "輸出規制",
            "CHIPS法", "半導体補助金",
            "iPhone", "スマホ出荷", "PC出荷",
            "メモリ在庫", "DRAM", "NAND",
            "半導体市況", "シリコンサイクル",
        ]

        # 三菱重工・川崎重工: 国策・防衛・エネルギー
        heavy_ind = [
            "三菱重工", "7011", "川崎重工", "7012", "IHI",
            "防衛省", "防衛費", "防衛装備",
            "トマホーク", "ミサイル", "反撃能力",
            "NATO", "地政学", "台湾有事",
            "原発再稼働", "次世代原子炉", "SMR",
            "水素", "液化水素", "サプライチェーン",
            "H3ロケット", "JAXA", "宇宙",
            "円安", "為替介入"
        ]

        # 三菱UFJ (8306): 金利・金融政策・株主還元
        ufj = [
            "三菱UFJ", "8306", "MUFG",
            "日銀", "植田総裁", "金融政策決定会合",
            "マイナス金利", "利上げ", "金利ある世界",
            "YCC", "イールドカーブ", "長期金利",
            "FRB", "パウエル", "米金利",
            "PBR1倍", "東証要請",
            "増配", "自社株買い", "総還元性向",
            "政策保有株", "持ち合い解消"
        ]

        self.MY_PORTFOLIO: List[str] = tokyo_ohka + heavy_ind + ufj

        # === 2. 新規チャンス発掘リスト（攻撃） ===
        opportunity_str = os.getenv("OPPORTUNITY_KEYWORDS",
            "上方修正,最高益,大幅増益,"
            "増配,株式分割,"
            "ストップ高,サプライズ,"
            "レーティング引き上げ,格上げ,強気,"
            "大量保有,アクティビスト,"
            "TOB,MBO,提携,買収,"
            "世界初,画期的")
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
        self.CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-haiku-20240307")

        # === State File ===
        self.LAST_SEEN_FILE = os.getenv("LAST_SEEN_FILE", "last_seen.txt")

        self._validate()

    def _load_rss_feeds(self) -> List[str]:
        """Load RSS feeds from env or use defaults"""
        custom_feeds = os.getenv("RSS_FEEDS")
        if custom_feeds:
            return [f.strip() for f in custom_feeds.split(",") if f.strip()]

        return [
            # === 日本国内メディア（日本語） ===
            # Yahoo!ニュース - ビジネス
            "https://news.yahoo.co.jp/rss/topics/business.xml",
            # Yahoo!ニュース - ビジネス（カテゴリ版）
            "https://news.yahoo.co.jp/rss/categories/business.xml",
            # 財経新聞（日本株専門、決算速報に強い）
            "https://www.zaikei.co.jp/rss/",

            # === グローバルメディア（日本語） ===
            # Investing.com 日本（世界のマーケット情報）
            "https://jp.investing.com/rss/news.rss",
            # ロイター日本語（wor.jp経由）
            "https://assets.wor.jp/rss/rdf/reuters/top.rdf",
            # ITmedia ビジネス
            "https://rss.itmedia.co.jp/rss/2.0/business_articles.xml",

            # === 保有株専用フィード（URLエンコード済み） ===
            "https://news.google.com/rss/search?q=%E6%9D%B1%E4%BA%AC%E5%BF%9C%E5%8C%96+OR+4186&hl=ja&gl=JP&ceid=JP:ja",
            "https://news.google.com/rss/search?q=%E4%B8%89%E8%8F%B1%E9%87%8D%E5%B7%A5+OR+7011&hl=ja&gl=JP&ceid=JP:ja",
            "https://news.google.com/rss/search?q=%E5%B7%9D%E5%B4%8E%E9%87%8D%E5%B7%A5+OR+7012&hl=ja&gl=JP&ceid=JP:ja",
            "https://news.google.com/rss/search?q=%E4%B8%89%E8%8F%B1UFJ+OR+8306&hl=ja&gl=JP&ceid=JP:ja",

            # === テーマ別（急騰材料）===
            "https://news.google.com/rss/search?q=%E5%8D%8A%E5%B0%8E%E4%BD%93+OR+%E6%B1%BA%E7%AE%97+OR+%E4%B8%8A%E6%96%B9%E4%BF%AE%E6%AD%A3&hl=ja&gl=JP&ceid=JP:ja",
            # 防衛・地政学テーマ
            "https://news.google.com/rss/search?q=%E9%98%B2%E8%A1%9B+OR+%E9%98%B2%E8%A1%9B%E8%B2%BB&hl=ja&gl=JP&ceid=JP:ja",
            # 日銀・金利テーマ
            "https://news.google.com/rss/search?q=%E6%97%A5%E9%8A%80+OR+%E9%87%91%E5%88%A9+OR+%E5%88%A9%E4%B8%8A%E3%81%92&hl=ja&gl=JP&ceid=JP:ja",

            # === グローバル半導体サプライチェーン（連想分析用）===
            # NVIDIA / エヌビディア
            "https://news.google.com/rss/search?q=NVIDIA%20OR%20%E3%82%A8%E3%83%8C%E3%83%93%E3%83%87%E3%82%A3%E3%82%A2&hl=ja&gl=JP&ceid=JP:ja",
            # SOX指数 / フィラデルフィア半導体
            "https://news.google.com/rss/search?q=SOX%E6%8C%87%E6%95%B0%20OR%20%E3%83%95%E3%82%A3%E3%83%A9%E3%83%87%E3%83%AB%E3%83%95%E3%82%A3%E3%82%A2%E5%8D%8A%E5%B0%8E%E4%BD%93&hl=ja&gl=JP&ceid=JP:ja",
            # Intel / AMD / TSMC
            "https://news.google.com/rss/search?q=Intel%20OR%20AMD%20OR%20TSMC%20%E5%8D%8A%E5%B0%8E%E4%BD%93&hl=ja&gl=JP&ceid=JP:ja",
            # AI半導体 / GPU / データセンター
            "https://news.google.com/rss/search?q=AI%E5%8D%8A%E5%B0%8E%E4%BD%93%20OR%20GPU%20OR%20%E3%83%87%E3%83%BC%E3%82%BF%E3%82%BB%E3%83%B3%E3%82%BF%E3%83%BC&hl=ja&gl=JP&ceid=JP:ja",
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
