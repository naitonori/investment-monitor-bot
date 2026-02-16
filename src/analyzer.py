"""
AI Analyzer Module - The Brain (Claude-powered)
Verdict (STRONG_BUY/BUY/WAIT/SELL) + Timeframe (DAY_TRADE/MID_LONG) を判定
"""
import json
from enum import Enum
from anthropic import Anthropic, APIError, APITimeoutError
from pydantic import BaseModel, Field
from typing import Dict, Optional
from loguru import logger
from config import config


# === Pydantic Models ===

class Verdict(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WAIT = "WAIT"
    SELL = "SELL"


class Timeframe(str, Enum):
    DAY_TRADE = "DAY_TRADE"
    MID_LONG = "MID_LONG"


class AnalysisResult(BaseModel):
    """AI分析の出力スキーマ"""
    verdict: Verdict = Field(description="投資判断: STRONG_BUY, BUY, WAIT, SELL")
    timeframe: Timeframe = Field(description="投資期間: DAY_TRADE(短期) or MID_LONG(中長期)")
    reason: str = Field(description="判断理由を1文で簡潔に", max_length=200)


# === Analyzer ===

class NewsAnalyzer:
    """Claude-powered analyzer with Verdict + Timeframe judgement"""

    SYSTEM_PROMPT = """あなたはプロのトレーダー兼投資アナリストです。
日本株市場に精通しており、ニュースから瞬時に投資判断と最適な保有期間を判定できます。

必ず以下のJSON形式のみで回答してください。それ以外のテキストは一切出力しないでください。

{
  "verdict": "STRONG_BUY" | "BUY" | "WAIT" | "SELL",
  "timeframe": "DAY_TRADE" | "MID_LONG",
  "reason": "判断理由を1文で簡潔に（日本語）"
}

【verdict の判断基準】
- STRONG_BUY: 上方修正、サプライズ決算、大型提携など、株価に強烈なインパクトがあるもの
- BUY: 業績好調、増配、国策テーマなど、ポジティブだが緊急性は低いもの
- WAIT: 判断材料不足、中立的なニュース
- SELL: 業績悪化、不祥事、下方修正など、ネガティブなもの

【timeframe の判断基準】
- DAY_TRADE: 決算速報、上方修正、提携発表、突発的な材料など瞬発力があるもの。翌営業日のギャップアップ/ダウンが予想される場合はこちら。
- MID_LONG: 国策（防衛費増額）、新工場建設、技術革新、業績の安定的拡大など。数週間〜数ヶ月の保有を推奨するもの。"""

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            logger.error("ANTHROPIC_API_KEY not set - analyzer disabled")
            self.client = None
        else:
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
            logger.success("Claude API client initialized")

    def analyze(self, news_item: Dict[str, str]) -> Optional[AnalysisResult]:
        """Analyze a news item and return structured AnalysisResult"""
        if not self.client:
            return None

        title = news_item.get("title", "")
        summary = news_item.get("summary", "")
        category = news_item.get("category", "unknown")
        matched_kw = news_item.get("matched_keywords", "")

        logger.info(f"Analyzing: {title[:60]}...")

        try:
            user_prompt = self._build_prompt(title, summary, category, matched_kw)

            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=300,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            raw_text = response.content[0].text.strip()
            result = self._parse_response(raw_text)

            if result:
                logger.success(
                    f"Analysis: {result.verdict.value} / {result.timeframe.value}"
                )
            return result

        except APITimeoutError:
            logger.error(f"Claude API timeout: {title[:40]}")
            return None
        except APIError as e:
            logger.error(f"Claude API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected analysis error: {e}")
            return None

    def _build_prompt(
        self, title: str, summary: str, category: str, matched_kw: str
    ) -> str:
        category_label = (
            "【保有株関連ニュース】" if category == "portfolio"
            else "【新規チャンス候補】"
        )

        return f"""{category_label}

【タイトル】
{title}

【概要】
{summary}

【マッチしたキーワード】
{matched_kw}

上記ニュースを分析し、投資判断(verdict)と最適な保有期間(timeframe)をJSON形式で回答してください。"""

    def _parse_response(self, raw: str) -> Optional[AnalysisResult]:
        """Parse Claude's JSON response into AnalysisResult"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = raw
            if "```" in raw:
                lines = raw.split("\n")
                json_lines = []
                in_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_block = not in_block
                        continue
                    if in_block:
                        json_lines.append(line)
                json_str = "\n".join(json_lines)

            data = json.loads(json_str)
            return AnalysisResult(**data)

        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e} | raw: {raw[:100]}")
            return self._fallback_parse(raw)
        except Exception as e:
            logger.warning(f"Pydantic validation failed: {e}")
            return self._fallback_parse(raw)

    def _fallback_parse(self, raw: str) -> Optional[AnalysisResult]:
        """Fallback parser for non-JSON responses"""
        try:
            raw_upper = raw.upper()

            # Detect verdict
            if "STRONG_BUY" in raw_upper:
                verdict = Verdict.STRONG_BUY
            elif "SELL" in raw_upper:
                verdict = Verdict.SELL
            elif "BUY" in raw_upper:
                verdict = Verdict.BUY
            else:
                verdict = Verdict.WAIT

            # Detect timeframe
            if "DAY_TRADE" in raw_upper:
                timeframe = Timeframe.DAY_TRADE
            else:
                timeframe = Timeframe.MID_LONG

            # Extract reason
            reason = raw[:150].replace("\n", " ").strip()
            for prefix in ["reason", "理由"]:
                if prefix in raw.lower():
                    parts = raw.split(":", 1)
                    if len(parts) > 1:
                        reason = parts[1].strip()[:150]
                        break

            return AnalysisResult(
                verdict=verdict,
                timeframe=timeframe,
                reason=reason or "分析結果を自動判定しました",
            )
        except Exception as e:
            logger.error(f"Fallback parse also failed: {e}")
            return None

    def health_check(self) -> bool:
        return self.client is not None
