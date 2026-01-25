# api/scanner/fast_scan.py

"""
Fast market scanner - scans thousands of stocks for basic metrics
Runs in background every 30 minutes
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import Optional
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from api.scanner.database import ScannerDB
from api.scanner.stock_universe import get_full_universe, UNIVERSE_SUMMARY

logger = logging.getLogger(__name__)


class FastScanner:
    """
    Fast scanner for market-wide stock screening
    
    Tier 1 scan - captures basic metrics for all stocks:
    - Price, change %
    - Volume, relative volume
    - 52-week high/low
    - Market cap category
    - Sector/Industry
    """
    
    def __init__(self, db: ScannerDB = None):
        self.db = db or ScannerDB()
        self.batch_size = 50  # yfinance works well with batches of ~50
        self.max_workers = 4  # Parallel threads for fetching
    
    def get_stock_universe(self) -> list[str]:
        """
        Get list of stocks to scan from curated universe
        
        Total: ~1,500 stocks including:
        - S&P 500 (large cap)
        - S&P 400 / Mid caps
        - Popular small/micro caps
        - Major ETFs
        """
        symbols = get_full_universe()
        
        logger.info(f"Stock universe: {len(symbols)} symbols")
        logger.info(f"  Large: {UNIVERSE_SUMMARY['sp500_largecap']}, "
                   f"Mid: {UNIVERSE_SUMMARY['sp400_midcap']}, "
                   f"Small: {UNIVERSE_SUMMARY['sp600_smallcap']}, "
                   f"ETFs: {UNIVERSE_SUMMARY['etfs']}")
        
        return symbols
    
    def _categorize_market_cap(self, market_cap: float) -> str:
        """Categorize market cap"""
        if not market_cap:
            return "unknown"
        
        if market_cap >= 200_000_000_000:  # $200B+
            return "mega"
        elif market_cap >= 10_000_000_000:  # $10B+
            return "large"
        elif market_cap >= 2_000_000_000:  # $2B+
            return "mid"
        elif market_cap >= 300_000_000:  # $300M+
            return "small"
        else:
            return "micro"
    
    def _scan_batch(self, symbols: list[str]) -> list[dict]:
        """Scan a batch of symbols"""
        results = []
        
        try:
            # Fetch data for all symbols in batch
            tickers = yf.Tickers(" ".join(symbols))
            
            for symbol in symbols:
                try:
                    ticker = tickers.tickers.get(symbol)
                    if not ticker:
                        continue
                    
                    info = ticker.info
                    if not info or 'regularMarketPrice' not in info:
                        continue
                    
                    # Get historical data for volume average
                    hist = ticker.history(period="1mo")
                    if hist.empty:
                        continue
                    
                    # Calculate metrics
                    current_price = info.get('regularMarketPrice') or info.get('currentPrice')
                    prev_close = info.get('regularMarketPreviousClose') or info.get('previousClose')
                    current_volume = info.get('regularMarketVolume') or info.get('volume', 0)
                    
                    if not current_price or not prev_close:
                        continue
                    
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    # Volume average from history
                    avg_volume = hist['Volume'].tail(20).mean() if len(hist) >= 20 else hist['Volume'].mean()
                    relative_volume = current_volume / avg_volume if avg_volume > 0 else 0
                    
                    # 52-week high/low
                    week_52_high = info.get('fiftyTwoWeekHigh')
                    week_52_low = info.get('fiftyTwoWeekLow')
                    
                    dist_from_high = None
                    dist_from_low = None
                    if week_52_high and current_price:
                        dist_from_high = ((current_price - week_52_high) / week_52_high) * 100
                    if week_52_low and current_price:
                        dist_from_low = ((current_price - week_52_low) / week_52_low) * 100
                    
                    # Market cap
                    market_cap = info.get('marketCap')
                    
                    results.append({
                        "symbol": symbol,
                        "company_name": info.get('shortName') or info.get('longName'),
                        "price": current_price,
                        "change_percent": round(change_pct, 2),
                        "volume": current_volume,
                        "avg_volume_20d": round(avg_volume) if avg_volume else None,
                        "relative_volume": round(relative_volume, 2),
                        "market_cap": market_cap,
                        "market_cap_category": self._categorize_market_cap(market_cap),
                        "sector": info.get('sector'),
                        "industry": info.get('industry'),
                        "week_52_high": week_52_high,
                        "week_52_low": week_52_low,
                        "distance_from_52w_high": round(dist_from_high, 2) if dist_from_high else None,
                        "distance_from_52w_low": round(dist_from_low, 2) if dist_from_low else None,
                        "is_unusual_volume": relative_volume >= 2.0,
                        "is_near_high": dist_from_high is not None and dist_from_high >= -5,
                        "is_near_low": dist_from_low is not None and dist_from_low <= 10,
                    })
                    
                except Exception as e:
                    logger.debug(f"Error scanning {symbol}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"Error scanning batch: {e}")
        
        return results
    
    def run_scan(self, symbols: list[str] = None, progress_callback=None) -> dict:
        """
        Run full market scan
        
        Args:
            symbols: List of symbols to scan (default: full universe)
            progress_callback: Optional callback(scanned, total, current_symbol)
        
        Returns:
            dict with scan results summary
        """
        started_at = datetime.now(timezone.utc)
        
        if symbols is None:
            symbols = self.get_stock_universe()
        
        total = len(symbols)
        logger.info(f"Starting fast scan of {total} stocks...")
        
        # Split into batches
        batches = [symbols[i:i + self.batch_size] for i in range(0, total, self.batch_size)]
        
        all_results = []
        scanned = 0
        
        # Process batches with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._scan_batch, batch): batch for batch in batches}
            
            for future in as_completed(futures):
                batch = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                    scanned += len(batch)
                    
                    if progress_callback:
                        progress_callback(scanned, total, batch[0] if batch else None)
                    
                    logger.debug(f"Progress: {scanned}/{total} ({len(results)} with data)")
                    
                except Exception as e:
                    logger.warning(f"Batch failed: {e}")
                    scanned += len(batch)
        
        # Store results in database
        if all_results:
            self.db.bulk_upsert(all_results)
        
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()
        
        # Log scan
        self.db.log_scan(
            scan_type="fast_scan",
            started_at=started_at,
            completed_at=completed_at,
            stocks_scanned=total,
            stocks_with_data=len(all_results)
        )
        
        summary = {
            "status": "completed",
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_seconds": round(duration, 1),
            "stocks_scanned": total,
            "stocks_with_data": len(all_results),
            "unusual_volume": len([r for r in all_results if r.get("is_unusual_volume")]),
            "near_52w_high": len([r for r in all_results if r.get("is_near_high")]),
            "big_movers": len([r for r in all_results if abs(r.get("change_percent", 0)) > 5]),
        }
        
        logger.info(f"Scan completed: {summary}")
        return summary
    
    def quick_scan(self, symbols: list[str]) -> list[dict]:
        """
        Quick scan of specific symbols (for testing)
        Returns results directly without storing
        """
        return self._scan_batch(symbols)

