"""
Main Entry Point - The Immortal Loop
絶対に停止しない24/7投資監視システム v2.0
Verdict (STRONG_BUY/BUY/WAIT/SELL) + Timeframe (DAY_TRADE/MID_LONG)
"""
import time
import sys
from datetime import datetime
from loguru import logger

from config import config
from fetcher import NewsFetcher
from analyzer import NewsAnalyzer, Verdict
from notifier import DiscordNotifier


class InvestmentMonitorBot:
    """The main bot orchestrator - designed to NEVER crash"""

    def __init__(self):
        # Configure loguru
        logger.remove()
        logger.add(
            sys.stderr,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<level>{message}</level>"
            ),
            level="INFO",
        )
        logger.add(
            "bot.log",
            rotation="10 MB",
            retention="7 days",
            level="DEBUG",
        )

        logger.info("=" * 60)
        logger.info("Investment Monitor Bot v2.0 - Initializing...")
        logger.info("=" * 60)

        try:
            self.fetcher = NewsFetcher()
            self.analyzer = NewsAnalyzer()
            self.notifier = DiscordNotifier()
            logger.success("All components initialized")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            # Initialize with None - will degrade gracefully
            self.fetcher = None
            self.analyzer = None
            self.notifier = None

        logger.info(config)

        self.stats = {
            "loops": 0,
            "news_found": 0,
            "analyzed": 0,
            "strong_buys": 0,
            "errors": 0,
            "start_time": datetime.now(),
        }

    def run(self):
        """THE IMMORTAL LOOP - NEVER STOPS"""
        logger.info("Starting immortal loop...")

        # Startup notification
        try:
            if self.notifier:
                self.notifier.send_startup_notification()
        except Exception as e:
            logger.error(f"Startup notification failed: {e}")

        while True:
            try:
                self._run_single_iteration()
            except KeyboardInterrupt:
                logger.warning("Keyboard interrupt - shutting down")
                self._shutdown()
                break
            except Exception as e:
                logger.error(f"CRITICAL LOOP ERROR: {e}")
                logger.exception("Full traceback:")
                self.stats["errors"] += 1

                try:
                    if self.notifier:
                        self.notifier.send_error_alert(str(e))
                except Exception:
                    pass

            finally:
                time.sleep(config.INTERVAL_SECONDS)

    def _run_single_iteration(self):
        self.stats["loops"] += 1
        loop_num = self.stats["loops"]

        logger.info(f"--- Loop #{loop_num} | {datetime.now():%Y-%m-%d %H:%M:%S} ---")

        # Step 1: Fetch
        if not self.fetcher:
            logger.error("Fetcher not available")
            return

        try:
            news_items = self.fetcher.fetch_all_news()
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            return

        if not news_items:
            logger.info("No new matching news")
            return

        self.stats["news_found"] += len(news_items)
        logger.success(f"Found {len(news_items)} new items")

        # Step 2: Analyze & Notify
        for idx, item in enumerate(news_items, 1):
            try:
                logger.info(
                    f"[{idx}/{len(news_items)}] {item['title'][:60]}..."
                )

                if not self.analyzer:
                    logger.error("Analyzer not available")
                    continue

                analysis = self.analyzer.analyze(item)
                if not analysis:
                    logger.warning("Analysis returned None - skipping")
                    continue

                self.stats["analyzed"] += 1

                # Track STRONG_BUY count
                if analysis.verdict == Verdict.STRONG_BUY:
                    self.stats["strong_buys"] += 1

                # Skip WAIT notifications to reduce noise
                if analysis.verdict == Verdict.WAIT:
                    logger.info("Verdict=WAIT - notification suppressed")
                    continue

                # Notify
                if self.notifier:
                    try:
                        self.notifier.send_analysis_alert(item, analysis)
                    except Exception as e:
                        logger.error(f"Notification failed: {e}")

                # Rate limit protection
                time.sleep(2)

            except Exception as e:
                logger.error(f"Failed to process item {idx}: {e}")
                continue

        self._log_stats()

    def _log_stats(self):
        uptime = datetime.now() - self.stats["start_time"]
        logger.info(
            f"Stats: loops={self.stats['loops']}, "
            f"found={self.stats['news_found']}, "
            f"analyzed={self.stats['analyzed']}, "
            f"strong_buys={self.stats['strong_buys']}, "
            f"errors={self.stats['errors']}, "
            f"uptime={uptime}"
        )

    def _shutdown(self):
        logger.info("Shutting down...")
        self._log_stats()
        logger.info("Goodbye!")


def main():
    try:
        bot = InvestmentMonitorBot()
        bot.run()
    except Exception as e:
        logger.critical(f"FATAL: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
