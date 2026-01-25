# api/scanner/alpaca_scan.py

"""
Alpaca-powered market scanner
Much more reliable than yfinance for bulk scanning

Rate limits: 200 requests/minute (free tier)
Using bulk endpoints: Can scan 7000+ stocks in ~35 requests
"""

import requests
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from api.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_DATA_URL
from api.scanner.database import ScannerDB
from api.scanner.stock_universe import get_full_universe

logger = logging.getLogger(__name__)


class AlpacaScanner:
    """
    Fast scanner using Alpaca Market Data API
    
    Uses bulk endpoints:
    - /v2/stocks/snapshots - Get quotes for up to 200 symbols at once
    - /v2/stocks/bars - Get historical bars for multiple symbols
    
    Rate limit: 200 req/min = can scan 7000+ stocks in ~2-3 minutes
    """
    
    def __init__(self, db: ScannerDB = None):
        self.db = db or ScannerDB()
        self.headers = {
            "APCA-API-KEY-ID": ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
        }
        self.data_url = ALPACA_DATA_URL
        self.batch_size = 200  # Alpaca allows up to 200 symbols per request
        self.request_delay = 0.35  # ~170 req/min to stay under 200 limit
    
    def _get_snapshots(self, symbols: list[str]) -> dict:
        """
        Get snapshots (latest quote + daily bar) for multiple symbols
        
        Returns dict: {symbol: snapshot_data}
        """
        url = f"{self.data_url}/v2/stocks/snapshots"
        params = {"symbols": ",".join(symbols)}
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited, waiting 60s...")
                time.sleep(60)
                return self._get_snapshots(symbols)  # Retry
            else:
                logger.warning(f"Snapshot error {response.status_code}: {response.text[:100]}")
                return {}
                
        except Exception as e:
            logger.error(f"Snapshot request failed: {e}")
            return {}
    
    def _get_bars_bulk(self, symbols: list[str], days: int = 20) -> dict:
        """
        Get historical bars for multiple symbols (for calculating avg volume)
        
        Note: Free tier may not have access to historical bars - that's OK,
        we'll calculate relative volume from the snapshot data instead.
        
        Returns dict: {symbol: [bars]}
        """
        url = f"{self.data_url}/v2/stocks/bars"
        
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days + 5)  # Extra days for weekends
        
        params = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "start": start.strftime("%Y-%m-%dT00:00:00Z"),
            "end": end.strftime("%Y-%m-%dT23:59:59Z"),
            "limit": 10000,
            "adjustment": "split",
        }
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("bars", {})
            elif response.status_code == 429:
                logger.warning("Rate limited on bars, waiting 60s...")
                time.sleep(60)
                return self._get_bars_bulk(symbols, days)
            elif response.status_code == 403:
                # Free tier doesn't have historical bars - that's OK
                logger.debug("Historical bars not available (free tier)")
                return {}
            else:
                logger.debug(f"Bars endpoint returned {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Bars request failed: {e}")
            return {}
    
    def _get_assets(self) -> dict:
        """Get asset info (sector, industry, name) from Alpaca"""
        url = f"https://paper-api.alpaca.markets/v2/assets"
        params = {"status": "active", "asset_class": "us_equity"}
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                assets = response.json()
                return {a["symbol"]: a for a in assets}
            return {}
        except:
            return {}
    
    def _categorize_market_cap(self, market_cap: float) -> str:
        """Categorize market cap"""
        if not market_cap:
            return "unknown"
        
        if market_cap >= 200_000_000_000:
            return "mega"
        elif market_cap >= 10_000_000_000:
            return "large"
        elif market_cap >= 2_000_000_000:
            return "mid"
        elif market_cap >= 300_000_000:
            return "small"
        else:
            return "micro"
    
    def _process_batch(self, symbols: list[str], asset_info: dict) -> list[dict]:
        """Process a batch of symbols"""
        results = []
        
        # Get snapshots (current price data)
        snapshots = self._get_snapshots(symbols)
        if not snapshots:
            return results
        
        time.sleep(self.request_delay)
        
        # Get historical bars for avg volume
        bars = self._get_bars_bulk(symbols)
        
        time.sleep(self.request_delay)
        
        for symbol in symbols:
            try:
                snap = snapshots.get(symbol)
                if not snap:
                    continue
                
                daily = snap.get("dailyBar", {})
                prev = snap.get("prevDailyBar", {})
                latest = snap.get("latestTrade", {})
                
                if not daily or not prev:
                    continue
                
                # Current price and change
                current_price = daily.get("c") or latest.get("p")
                prev_close = prev.get("c")
                
                if not current_price or not prev_close:
                    continue
                
                change_pct = ((current_price - prev_close) / prev_close) * 100
                
                # Volume
                current_volume = daily.get("v", 0)
                
                # Calculate average volume from bars
                symbol_bars = bars.get(symbol, [])
                if symbol_bars and len(symbol_bars) > 1:
                    volumes = [b.get("v", 0) for b in symbol_bars[:-1]]  # Exclude today
                    avg_volume = sum(volumes) / len(volumes) if volumes else 0
                else:
                    avg_volume = current_volume
                
                relative_volume = current_volume / avg_volume if avg_volume > 0 else 0
                
                # 52-week high/low (from bars if available, approximate)
                all_highs = [b.get("h", 0) for b in symbol_bars]
                all_lows = [b.get("l", float("inf")) for b in symbol_bars if b.get("l")]
                
                week_52_high = max(all_highs) if all_highs else current_price
                week_52_low = min(all_lows) if all_lows else current_price
                
                dist_from_high = ((current_price - week_52_high) / week_52_high) * 100 if week_52_high else None
                dist_from_low = ((current_price - week_52_low) / week_52_low) * 100 if week_52_low else None
                
                # Asset info
                asset = asset_info.get(symbol, {})
                
                results.append({
                    "symbol": symbol,
                    "company_name": asset.get("name"),
                    "price": round(current_price, 2),
                    "change_percent": round(change_pct, 2),
                    "volume": current_volume,
                    "avg_volume_20d": round(avg_volume) if avg_volume else None,
                    "relative_volume": round(relative_volume, 2),
                    "market_cap": None,  # Alpaca doesn't provide this
                    "market_cap_category": "unknown",
                    "sector": None,  # Would need another data source
                    "industry": None,
                    "week_52_high": round(week_52_high, 2) if week_52_high else None,
                    "week_52_low": round(week_52_low, 2) if week_52_low else None,
                    "distance_from_52w_high": round(dist_from_high, 2) if dist_from_high else None,
                    "distance_from_52w_low": round(dist_from_low, 2) if dist_from_low else None,
                    "is_unusual_volume": relative_volume >= 2.0,
                    "is_near_high": dist_from_high is not None and dist_from_high >= -5,
                    "is_near_low": dist_from_low is not None and dist_from_low <= 10,
                })
                
            except Exception as e:
                logger.debug(f"Error processing {symbol}: {e}")
                continue
        
        return results
    
    def run_scan(self, symbols: list[str] = None, progress_callback=None) -> dict:
        """
        Run full market scan using Alpaca
        
        Args:
            symbols: List of symbols to scan (default: full universe)
            progress_callback: Optional callback(scanned, total, current_symbol)
        
        Returns:
            dict with scan results summary
        """
        started_at = datetime.now(timezone.utc)
        
        if symbols is None:
            symbols = get_full_universe()
        
        total = len(symbols)
        logger.info(f"🚀 Starting Alpaca scan of {total} stocks...")
        
        # Get asset info first
        logger.info("  Fetching asset info...")
        asset_info = self._get_assets()
        logger.info(f"  Got info for {len(asset_info)} assets")
        
        # Split into batches
        batches = [symbols[i:i + self.batch_size] for i in range(0, total, self.batch_size)]
        logger.info(f"  Processing {len(batches)} batches of {self.batch_size} symbols...")
        
        all_results = []
        scanned = 0
        
        for i, batch in enumerate(batches):
            try:
                results = self._process_batch(batch, asset_info)
                all_results.extend(results)
                scanned += len(batch)
                
                # Save progress incrementally
                if results:
                    self.db.bulk_upsert(results)
                
                if progress_callback:
                    progress_callback(scanned, total, batch[0] if batch else None)
                
                # Log progress every 10 batches
                if (i + 1) % 10 == 0:
                    logger.info(f"  Progress: {scanned}/{total} ({len(all_results)} with data)")
                
            except Exception as e:
                logger.warning(f"Batch {i} failed: {e}")
                scanned += len(batch)
        
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - started_at).total_seconds()
        
        # Log scan
        self.db.log_scan(
            scan_type="alpaca_scan",
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
        
        logger.info(f"✅ Alpaca scan completed: {summary}")
        return summary


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scanner = AlpacaScanner()
    
    # Test with a small batch
    test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "AMD", "INTC", "NFLX"]
    
    print(f"\nTesting Alpaca scanner with {len(test_symbols)} symbols...")
    result = scanner.run_scan(symbols=test_symbols)
    
    print(f"\nResults: {result}")

