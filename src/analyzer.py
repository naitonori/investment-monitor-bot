"""
AI Analyzer Module - The Brain (Claude-powered)
Verdict + Timeframe + O'Neil Advice
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
    ticker: str = Field(description="銘柄名と証券コード（例: 東京応化工業(4186)）", max_length=100)
    verdict: Verdict = Field(description="投資判断")
    timeframe: Timeframe = Field(description="投資期間")
    holding_action: str = Field(description="保有株への具体的アクション", max_length=100, default="")
    reason: str = Field(description="判断理由", max_length=200)
    oneil_advice: str = Field(description="オニールならどうするか", max_length=200)


# === Analyzer ===

class NewsAnalyzer:
    """Claude-powered analyzer with O'Neil perspective"""

    SYSTEM_PROMPT = """あなたは日本株専門のプロトレーダーです。
ニュース内容から「どの株が上がるか/下がるか」「デイトレ向きか中期保有向きか」を即座に判断できます。

【重要】ユーザーは以下の銘柄を保有しています:
- 川崎重工業 (7012)
- 東京応化工業 (4186)
- 三菱重工業 (7011)

保有株に関するネガティブニュース（暴落、下落、業績悪化、不祥事、格下げ等）が出た場合は、
必ずSELLの判定を出して警告してください。これは非常に重要です。

さらに、あなたはウィリアム・オニール（CAN-SLIM投資法の創始者）の思考を完璧に理解しています。
オニールなら、このニュースを見てどう行動するかを予想してアドバイスしてください。

【オニールの基本原則（CAN-SLIM）】
- C: Current Earnings（直近の四半期EPS成長率25%以上）
- A: Annual Earnings（年間EPS成長率25%以上が3年以上）
- N: New（新製品・新経営陣・新高値）
- S: Supply and Demand（出来高の急増は機関投資家の参入サイン）
- L: Leader or Laggard（業界のリーダー株を買え、出遅れ株は避けろ）
- I: Institutional Sponsorship（優良ファンドが買っているか）
- M: Market Direction（市場全体のトレンドに逆らうな）

【オニールの損切りルール】
- 買値から8%下落したら、理由を問わず損切り
- 利益が出ている株は、20-25%で利確を検討
- ただし大化け株は持ち続ける（利益を伸ばせ）

必ず以下のJSON形式のみで回答してください。それ以外のテキストは一切出力しないでください。

{
  "ticker": "銘柄名(証券コード)",
  "verdict": "STRONG_BUY" | "BUY" | "WAIT" | "SELL",
  "timeframe": "DAY_TRADE" | "MID_LONG",
  "holding_action": "保有株への具体的アクション（下記参照）",
  "reason": "このニュースでどの株が上がる/下がるか、1文で簡潔に（日本語）",
  "oneil_advice": "オニールならこう言う、という1文のアドバイス（日本語）"
}

【ticker の書き方】
- 必ず「銘柄名(証券コード)」の形式で書く。例: 東京応化工業(4186)
- 該当する銘柄が複数あれば全て書く。例: 三菱重工業(7011), 川崎重工業(7012)
- 証券コードがわからない場合は銘柄名だけでもOK

【holding_action の書き方】
保有株（川崎重工7012, 東京応化4186, 三菱重工7011）に関するニュースの場合:
- "ホールド継続" : 中期で持ち続けてOK
- "買い増し検討" : 押し目で追加購入チャンス
- "即売り（損切り）" : 大暴落・不祥事等、すぐに手放すべき
- "利確検討" : 十分利益が出ているなら利確タイミング
- "寄りで売り" : デイトレ観点で翌朝寄り付きで売るべき
- "様子見" : 方向感なし、焦る必要なし
保有株に関係ないニュースの場合は空文字""でOK

【verdict の判断基準】
- STRONG_BUY: 市場がまだ織り込んでいないサプライズ材料。出来高急増が予想される。
- BUY: ポジティブだが、すぐに飛び乗る必要はない。押し目で拾いたい水準。
- WAIT: 材料不足、または既に織り込み済み。
- SELL: ネガティブ材料。保有中なら損切り/利確を検討すべき。

【timeframe の判断基準】
- DAY_TRADE: 翌営業日に値動きが集中するタイプの材料（決算速報、上方修正、提携発表、突発ニュース）
- MID_LONG: 数週間〜数ヶ月かけてジワジワ効いてくるテーマ（国策、業界トレンド、構造変化）"""

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
        article_body = news_item.get("article_body", "")
        category = news_item.get("category", "unknown")
        matched_kw = news_item.get("matched_keywords", "")

        logger.info(f"Analyzing: {title[:60]}...")

        try:
            user_prompt = self._build_prompt(
                title, summary, article_body, category, matched_kw
            )

            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=500,
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
        self, title: str, summary: str, article_body: str,
        category: str, matched_kw: str
    ) -> str:
        category_label = (
            "【保有株関連ニュース】" if category == "portfolio"
            else "【新規チャンス候補】"
        )

        body_section = ""
        if article_body:
            body_section = f"""
【記事本文】
{article_body}
"""

        return f"""{category_label}

【タイトル】
{title}

【概要】
{summary}
{body_section}
【マッチしたキーワード】
{matched_kw}

このニュースから、どの株が上がる可能性があるかを分析してください。
デイトレ向きか中期保有向きかを判定し、オニール（CAN-SLIM）ならどうアドバイスするかを予想してください。"""

    def _parse_response(self, raw: str) -> Optional[AnalysisResult]:
        """Parse Claude's JSON response into AnalysisResult"""
        try:
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

            if "STRONG_BUY" in raw_upper:
                verdict = Verdict.STRONG_BUY
            elif "SELL" in raw_upper:
                verdict = Verdict.SELL
            elif "BUY" in raw_upper:
                verdict = Verdict.BUY
            else:
                verdict = Verdict.WAIT

            if "DAY_TRADE" in raw_upper:
                timeframe = Timeframe.DAY_TRADE
            else:
                timeframe = Timeframe.MID_LONG

            reason = raw[:150].replace("\n", " ").strip()

            return AnalysisResult(
                ticker="不明",
                verdict=verdict,
                timeframe=timeframe,
                holding_action="",
                reason=reason or "分析結果を自動判定しました",
                oneil_advice="オニール: 市場トレンドを確認してからエントリーせよ",
            )
        except Exception as e:
            logger.error(f"Fallback parse also failed: {e}")
            return None

    def health_check(self) -> bool:
        return self.client is not None
