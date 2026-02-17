"""
Discord Notifier Module - The Messenger
Verdict + Timeframe に応じた視覚的通知
"""
import requests
from typing import Dict
from datetime import datetime, timezone, timedelta
from loguru import logger
from config import config
from analyzer import AnalysisResult, Verdict, Timeframe

JST = timezone(timedelta(hours=9))


# === Icon Mapping ===

VERDICT_ICONS = {
    Verdict.STRONG_BUY: "\U0001f680 STRONG BUY",   # Rocket
    Verdict.BUY:        "\U0001f7e2 BUY",            # Green circle
    Verdict.WAIT:       "\u23f3 WAIT",                # Hourglass
    Verdict.SELL:       "\U0001f534 SELL",             # Red circle
}

TIMEFRAME_ICONS = {
    Timeframe.DAY_TRADE: "\u26a1\ufe0f [DAY TRADE]",   # Lightning
    Timeframe.MID_LONG:  "\U0001f331 [MID TERM]",      # Seedling
}

VERDICT_COLORS = {
    Verdict.STRONG_BUY: 0xFF4500,  # Orange-Red (urgent)
    Verdict.BUY:        0x00FF00,  # Green
    Verdict.WAIT:       0xFFAA00,  # Orange
    Verdict.SELL:       0xFF0000,  # Red
}


class DiscordNotifier:
    """Discord webhook notifier with rich Verdict + Timeframe display"""

    def __init__(self):
        self.webhook_url = config.DISCORD_WEBHOOK_URL
        if not self.webhook_url:
            logger.warning("DISCORD_WEBHOOK_URL not set - notifications disabled")

    def send_startup_notification(self):
        portfolio_kw = ", ".join(config.MY_PORTFOLIO[:5])
        opp_kw = ", ".join(config.OPPORTUNITY_KEYWORDS[:5])

        message = (
            "\U0001f916 **Investment Monitor Bot v2.0 Started**\n\n"
            f"\U0001f6e1\ufe0f Portfolio: {portfolio_kw}...\n"
            f"\U0001f4a1 Opportunity: {opp_kw}...\n"
            f"\u23f1\ufe0f Interval: {config.INTERVAL_SECONDS}s\n"
            f"\U0001f4e1 RSS feeds: {len(config.RSS_FEEDS)}\n\n"
            "\U0001f680 Bot is now running!"
        )
        return self.send_message(message)

    def send_analysis_alert(
        self, news_item: Dict[str, str], analysis: AnalysisResult
    ) -> bool:
        """Send rich analysis notification to Discord"""
        try:
            # Build header line
            timeframe_icon = TIMEFRAME_ICONS.get(
                analysis.timeframe, "\U0001f4ca"
            )
            verdict_icon = VERDICT_ICONS.get(
                analysis.verdict, "\U0001f4ca"
            )

            title = news_item.get("title", "No title")
            link = news_item.get("link", "")
            matched_kw = news_item.get("matched_keywords", "")
            category = news_item.get("category", "unknown")

            # Category label
            cat_label = (
                "\U0001f6e1\ufe0f Portfolio" if category == "portfolio"
                else "\U0001f4a1 Opportunity"
            )

            # Embed color
            color = VERDICT_COLORS.get(analysis.verdict, 0x888888)

            # Ticker info
            ticker = getattr(analysis, "ticker", "") or ""

            # Build Discord embed
            embed = {
                "title": f"{timeframe_icon} {verdict_icon}",
                "description": f"**{ticker}**\n{analysis.reason}" if ticker else analysis.reason,
                "url": link,
                "color": color,
                "fields": [
                    {
                        "name": "\U0001f4c8 銘柄",
                        "value": f"**{ticker}**" if ticker else "---",
                        "inline": True,
                    },
                    {
                        "name": "Verdict",
                        "value": f"**{analysis.verdict.value}**",
                        "inline": True,
                    },
                    {
                        "name": "Timeframe",
                        "value": f"**{analysis.timeframe.value}**",
                        "inline": True,
                    },
                    {
                        "name": "\U0001f4f0 ニュース",
                        "value": title[:120],
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": f"Keywords: {matched_kw[:80]} | Powered by Claude"
                },
            }

            # 記事の公開日時（日本時間）
            published_raw = news_item.get("published", "")
            if published_raw:
                pub_display = self._format_published(published_raw)
                embed["fields"].append({
                    "name": "\U0001f4c5 記事公開日時",
                    "value": pub_display,
                    "inline": True,
                })

            # O'Neil advice
            if hasattr(analysis, "oneil_advice") and analysis.oneil_advice:
                embed["fields"].append({
                    "name": "\U0001f4d6 O'Neil (CAN-SLIM)",
                    "value": analysis.oneil_advice,
                    "inline": False,
                })

            # Add urgency note for STRONG_BUY + DAY_TRADE
            if (
                analysis.verdict == Verdict.STRONG_BUY
                and analysis.timeframe == Timeframe.DAY_TRADE
            ):
                embed["fields"].append({
                    "name": "\u26a0\ufe0f URGENT",
                    "value": "**\u2192 \u7fcc\u55b6\u696d\u65e5\u306e\u5bc4\u308a\u4ed8\u304d\u3092\u30c1\u30a7\u30c3\u30af\uff01**",
                    "inline": False,
                })

            payload = {"embeds": [embed]}
            return self._send_webhook(payload)

        except Exception as e:
            logger.error(f"Failed to build Discord embed: {e}")
            # Fallback to plain text
            fallback = (
                f"{timeframe_icon} {verdict_icon}: {title}\n"
                f"{analysis.reason}\n{link}"
            )
            return self.send_message(fallback)

    def send_message(self, content: str) -> bool:
        payload = {"content": content}
        return self._send_webhook(payload)

    def send_error_alert(self, error_msg: str) -> bool:
        message = f"\u26a0\ufe0f **Error**\n```\n{error_msg[:1000]}\n```"
        return self.send_message(message)

    def _send_webhook(self, payload: dict) -> bool:
        if not self.webhook_url:
            logger.debug("Discord webhook not configured - skipping")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=config.HTTP_TIMEOUT,
            )

            if response.status_code == 204:
                logger.success("Discord notification sent")
                return True
            elif response.status_code == 429:
                logger.warning("Discord rate limited - skipped")
                return False
            else:
                logger.warning(f"Discord returned {response.status_code}")
                return False

        except requests.Timeout:
            logger.error("Discord webhook timeout")
            return False
        except requests.RequestException as e:
            logger.error(f"Discord webhook error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected Discord error: {e}")
            return False

    def _format_published(self, published_str: str) -> str:
        """公開日時を日本時間の読みやすい形式に変換"""
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(published_str)
            dt_jst = dt.astimezone(JST)
            return dt_jst.strftime("%m/%d %H:%M JST")
        except Exception:
            pass
        try:
            for fmt in ["%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S"]:
                try:
                    dt = datetime.strptime(published_str, fmt)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    dt_jst = dt.astimezone(JST)
                    return dt_jst.strftime("%m/%d %H:%M JST")
                except ValueError:
                    continue
        except Exception:
            pass
        return published_str[:20]

    def health_check(self) -> bool:
        return bool(self.webhook_url)
