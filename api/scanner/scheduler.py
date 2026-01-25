# api/scanner/scheduler.py

"""
Background scheduler for running market scans
Runs alongside the FastAPI server
"""

import asyncio
import threading
import logging
from datetime import datetime, timezone
from typing import Optional, Callable

from api.scanner.database import ScannerDB
from api.scanner.fast_scan import FastScanner
from api.scanner.alpaca_scan import AlpacaScanner

logger = logging.getLogger(__name__)


class ScannerScheduler:
    """
    Background scheduler that runs market scans at regular intervals
    
    Starts automatically with the FastAPI server and runs scans:
    - Every 30 minutes during market hours (9:30 AM - 4:00 PM ET)
    - Every 2 hours outside market hours
    """
    
    def __init__(self, interval_minutes: int = 30, use_alpaca: bool = True):
        self.interval_minutes = interval_minutes
        self.db = ScannerDB()
        self.use_alpaca = use_alpaca
        
        # Use Alpaca for more reliable bulk scanning (200 req/min vs Yahoo's ~500 before blocking)
        if use_alpaca:
            self.scanner = AlpacaScanner(self.db)
            logger.info("Using Alpaca scanner (faster, more reliable)")
        else:
            self.scanner = FastScanner(self.db)
            logger.info("Using yfinance scanner (slower, may hit rate limits)")
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_scan: Optional[datetime] = None
        self._scan_in_progress = False
    
    def start(self):
        """Start the background scheduler"""
        if self._running:
            logger.warning("Scanner scheduler already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"🔄 Scanner scheduler started (interval: {self.interval_minutes} mins)")
    
    def stop(self):
        """Stop the background scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scanner scheduler stopped")
    
    def _run_loop(self):
        """Main scheduler loop"""
        # Run initial scan after 10 seconds (let server start first)
        import time
        time.sleep(10)
        
        while self._running:
            try:
                # Check if we should run a scan
                if self._should_scan():
                    self._run_scan()
                
                # Sleep for 1 minute then check again
                for _ in range(60):  # Check every second for stop signal
                    if not self._running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait a minute on error
    
    def _should_scan(self) -> bool:
        """Determine if we should run a scan now"""
        if self._scan_in_progress:
            return False
        
        # If never scanned, scan now
        if self._last_scan is None:
            return True
        
        # Check time since last scan
        now = datetime.now(timezone.utc)
        minutes_since_last = (now - self._last_scan).total_seconds() / 60
        
        return minutes_since_last >= self.interval_minutes
    
    def _run_scan(self):
        """Execute a market scan"""
        self._scan_in_progress = True
        
        try:
            logger.info("🔍 Starting scheduled market scan...")
            
            def progress(scanned, total, symbol):
                if scanned % 100 == 0:
                    logger.info(f"  Scan progress: {scanned}/{total} ({symbol})")
            
            result = self.scanner.run_scan(progress_callback=progress)
            
            self._last_scan = datetime.now(timezone.utc)
            
            logger.info(f"✅ Scan complete: {result['stocks_with_data']} stocks, "
                       f"{result['unusual_volume']} unusual volume, "
                       f"{result['near_52w_high']} near highs")
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
        finally:
            self._scan_in_progress = False
    
    def trigger_scan_now(self) -> dict:
        """Manually trigger a scan (for API endpoint)"""
        if self._scan_in_progress:
            return {"status": "scan_in_progress", "message": "A scan is already running"}
        
        # Run in background thread
        threading.Thread(target=self._run_scan, daemon=True).start()
        
        return {
            "status": "started",
            "message": "Scan started in background",
            "last_scan": self._last_scan.isoformat() if self._last_scan else None
        }
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        return {
            "running": self._running,
            "scan_in_progress": self._scan_in_progress,
            "last_scan": self._last_scan.isoformat() if self._last_scan else None,
            "interval_minutes": self.interval_minutes,
            "db_stats": self.db.get_summary_stats()
        }


# Global scheduler instance
_scheduler: Optional[ScannerScheduler] = None


def get_scheduler() -> ScannerScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScannerScheduler(interval_minutes=30)
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Stop the global scheduler"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None

