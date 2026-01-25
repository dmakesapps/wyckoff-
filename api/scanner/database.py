# api/scanner/database.py

"""
SQLite database for storing scanner results
Provides fast queries for Kimi to access pre-computed market data
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import threading


class ScannerDB:
    """Thread-safe SQLite database for scanner results"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in project root
            db_path = Path(__file__).parent.parent.parent / "scanner_cache.db"
        self.db_path = str(db_path)
        self._local = threading.local()
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Main stocks table - fast scan data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                company_name TEXT,
                price REAL,
                change_percent REAL,
                volume INTEGER,
                avg_volume_20d REAL,
                relative_volume REAL,
                market_cap REAL,
                market_cap_category TEXT,
                sector TEXT,
                industry TEXT,
                week_52_high REAL,
                week_52_low REAL,
                distance_from_52w_high REAL,
                distance_from_52w_low REAL,
                is_unusual_volume INTEGER DEFAULT 0,
                is_near_high INTEGER DEFAULT 0,
                is_near_low INTEGER DEFAULT 0,
                last_updated TEXT
            )
        """)
        
        # Scan metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_metadata (
                id INTEGER PRIMARY KEY,
                scan_type TEXT,
                started_at TEXT,
                completed_at TEXT,
                stocks_scanned INTEGER,
                stocks_with_data INTEGER,
                duration_seconds REAL
            )
        """)
        
        # Create indexes for fast queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relative_volume ON stocks(relative_volume DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_change_percent ON stocks(change_percent DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_cap ON stocks(market_cap)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_unusual_volume ON stocks(is_unusual_volume)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_near_high ON stocks(is_near_high)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sector ON stocks(sector)")
        
        conn.commit()
    
    def upsert_stock(self, data: dict):
        """Insert or update a stock record"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO stocks (
                symbol, company_name, price, change_percent, volume,
                avg_volume_20d, relative_volume, market_cap, market_cap_category,
                sector, industry, week_52_high, week_52_low,
                distance_from_52w_high, distance_from_52w_low,
                is_unusual_volume, is_near_high, is_near_low, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("symbol"),
            data.get("company_name"),
            data.get("price"),
            data.get("change_percent"),
            data.get("volume"),
            data.get("avg_volume_20d"),
            data.get("relative_volume"),
            data.get("market_cap"),
            data.get("market_cap_category"),
            data.get("sector"),
            data.get("industry"),
            data.get("week_52_high"),
            data.get("week_52_low"),
            data.get("distance_from_52w_high"),
            data.get("distance_from_52w_low"),
            1 if data.get("is_unusual_volume") else 0,
            1 if data.get("is_near_high") else 0,
            1 if data.get("is_near_low") else 0,
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
    
    def bulk_upsert(self, stocks: list[dict]):
        """Bulk insert/update stocks"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        for data in stocks:
            cursor.execute("""
                INSERT OR REPLACE INTO stocks (
                    symbol, company_name, price, change_percent, volume,
                    avg_volume_20d, relative_volume, market_cap, market_cap_category,
                    sector, industry, week_52_high, week_52_low,
                    distance_from_52w_high, distance_from_52w_low,
                    is_unusual_volume, is_near_high, is_near_low, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("symbol"),
                data.get("company_name"),
                data.get("price"),
                data.get("change_percent"),
                data.get("volume"),
                data.get("avg_volume_20d"),
                data.get("relative_volume"),
                data.get("market_cap"),
                data.get("market_cap_category"),
                data.get("sector"),
                data.get("industry"),
                data.get("week_52_high"),
                data.get("week_52_low"),
                data.get("distance_from_52w_high"),
                data.get("distance_from_52w_low"),
                1 if data.get("is_unusual_volume") else 0,
                1 if data.get("is_near_high") else 0,
                1 if data.get("is_near_low") else 0,
                datetime.now(timezone.utc).isoformat()
            ))
        
        conn.commit()
    
    def log_scan(self, scan_type: str, started_at: datetime, completed_at: datetime, 
                 stocks_scanned: int, stocks_with_data: int):
        """Log scan metadata"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        duration = (completed_at - started_at).total_seconds()
        
        cursor.execute("""
            INSERT INTO scan_metadata (scan_type, started_at, completed_at, 
                                       stocks_scanned, stocks_with_data, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scan_type, started_at.isoformat(), completed_at.isoformat(),
              stocks_scanned, stocks_with_data, duration))
        conn.commit()
    
    # ═══════════════════════════════════════════════════════════════
    # QUERY METHODS (for Kimi tools)
    # ═══════════════════════════════════════════════════════════════
    
    def get_unusual_volume(self, min_rvol: float = 2.0, limit: int = 50, 
                           market_cap_category: str = None) -> list[dict]:
        """Get stocks with unusual volume"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM stocks 
            WHERE relative_volume >= ? 
            AND volume > 100000
        """
        params = [min_rvol]
        
        if market_cap_category:
            query += " AND market_cap_category = ?"
            params.append(market_cap_category)
        
        query += " ORDER BY relative_volume DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_gainers(self, limit: int = 50, min_volume: int = 100000,
                        market_cap_category: str = None) -> list[dict]:
        """Get top gaining stocks"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM stocks 
            WHERE change_percent > 0 
            AND volume >= ?
        """
        params = [min_volume]
        
        if market_cap_category:
            query += " AND market_cap_category = ?"
            params.append(market_cap_category)
        
        query += " ORDER BY change_percent DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_losers(self, limit: int = 50, min_volume: int = 100000,
                       market_cap_category: str = None) -> list[dict]:
        """Get top losing stocks"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM stocks 
            WHERE change_percent < 0 
            AND volume >= ?
        """
        params = [min_volume]
        
        if market_cap_category:
            query += " AND market_cap_category = ?"
            params.append(market_cap_category)
        
        query += " ORDER BY change_percent ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_near_52w_high(self, max_distance: float = 5.0, limit: int = 50,
                          market_cap_category: str = None) -> list[dict]:
        """Get stocks near 52-week high (potential breakouts)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM stocks 
            WHERE distance_from_52w_high >= ? 
            AND distance_from_52w_high <= 0
            AND volume > 100000
        """
        params = [-max_distance]
        
        if market_cap_category:
            query += " AND market_cap_category = ?"
            params.append(market_cap_category)
        
        query += " ORDER BY distance_from_52w_high DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_near_52w_low(self, max_distance: float = 10.0, limit: int = 50,
                         market_cap_category: str = None) -> list[dict]:
        """Get stocks near 52-week low (potential value or falling knife)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM stocks 
            WHERE distance_from_52w_low <= ? 
            AND distance_from_52w_low >= 0
            AND volume > 100000
        """
        params = [max_distance]
        
        if market_cap_category:
            query += " AND market_cap_category = ?"
            params.append(market_cap_category)
        
        query += " ORDER BY distance_from_52w_low ASC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_by_sector(self, sector: str, limit: int = 50,
                      sort_by: str = "change_percent") -> list[dict]:
        """Get stocks by sector"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        valid_sorts = ["change_percent", "relative_volume", "volume", "market_cap"]
        if sort_by not in valid_sorts:
            sort_by = "change_percent"
        
        cursor.execute(f"""
            SELECT * FROM stocks 
            WHERE sector = ?
            AND volume > 100000
            ORDER BY {sort_by} DESC 
            LIMIT ?
        """, (sector, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_stocks(self, 
                      min_price: float = None,
                      max_price: float = None,
                      min_volume: int = None,
                      min_rvol: float = None,
                      max_rvol: float = None,
                      min_change: float = None,
                      max_change: float = None,
                      market_cap_category: str = None,
                      sector: str = None,
                      limit: int = 100) -> list[dict]:
        """Flexible search with multiple filters"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        query = "SELECT * FROM stocks WHERE 1=1"
        params = []
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
        if min_volume is not None:
            query += " AND volume >= ?"
            params.append(min_volume)
        if min_rvol is not None:
            query += " AND relative_volume >= ?"
            params.append(min_rvol)
        if max_rvol is not None:
            query += " AND relative_volume <= ?"
            params.append(max_rvol)
        if min_change is not None:
            query += " AND change_percent >= ?"
            params.append(min_change)
        if max_change is not None:
            query += " AND change_percent <= ?"
            params.append(max_change)
        if market_cap_category:
            query += " AND market_cap_category = ?"
            params.append(market_cap_category)
        if sector:
            query += " AND sector = ?"
            params.append(sector)
        
        query += " ORDER BY relative_volume DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_scan_status(self) -> dict:
        """Get last scan status"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM scan_metadata 
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return {"status": "no_scans_yet"}
    
    def get_stock_count(self) -> int:
        """Get total stocks in database"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        return cursor.fetchone()[0]
    
    def get_summary_stats(self) -> dict:
        """Get summary statistics"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stats["total_stocks"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE is_unusual_volume = 1")
        stats["unusual_volume_count"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE is_near_high = 1")
        stats["near_52w_high_count"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE change_percent > 5")
        stats["big_gainers_count"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE change_percent < -5")
        stats["big_losers_count"] = cursor.fetchone()[0]
        
        # Last scan info
        cursor.execute("SELECT completed_at, stocks_with_data FROM scan_metadata ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            stats["last_scan"] = row[0]
            stats["last_scan_stocks"] = row[1]
        
        return stats
    
    # ═══════════════════════════════════════════════════════════════
    # FINVIZ-STYLE QUERIES
    # ═══════════════════════════════════════════════════════════════
    
    def get_market_breadth(self) -> dict:
        """Get market breadth (advancing vs declining)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE change_percent > 0")
        advancing = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE change_percent < 0")
        declining = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE change_percent = 0")
        unchanged = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE distance_from_52w_high >= -2")
        new_highs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE distance_from_52w_low <= 2")
        new_lows = cursor.fetchone()[0]
        
        total = advancing + declining + unchanged
        
        return {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "total": total,
            "advance_decline_ratio": round(advancing / declining, 2) if declining > 0 else 0,
            "advance_percent": round((advancing / total) * 100, 1) if total > 0 else 0,
            "decline_percent": round((declining / total) * 100, 1) if total > 0 else 0,
            "new_highs": new_highs,
            "new_lows": new_lows,
        }
    
    def get_sector_performance(self) -> list[dict]:
        """Get performance by sector (like Finviz sector heatmap)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                sector,
                COUNT(*) as stock_count,
                ROUND(AVG(change_percent), 2) as avg_change,
                ROUND(SUM(CASE WHEN change_percent > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as percent_advancing,
                ROUND(AVG(relative_volume), 2) as avg_rvol,
                SUM(volume) as total_volume,
                SUM(market_cap) as total_market_cap
            FROM stocks 
            WHERE sector IS NOT NULL AND sector != ''
            GROUP BY sector
            ORDER BY avg_change DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_heatmap_data(self, limit_per_sector: int = 20) -> dict:
        """Get data for heatmap visualization (like Finviz S&P 500 map)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        sectors = {}
        
        # Get unique sectors
        cursor.execute("SELECT DISTINCT sector FROM stocks WHERE sector IS NOT NULL AND sector != ''")
        sector_list = [row[0] for row in cursor.fetchall()]
        
        for sector in sector_list:
            cursor.execute("""
                SELECT 
                    symbol, company_name, price, change_percent, 
                    market_cap, market_cap_category, volume, relative_volume
                FROM stocks 
                WHERE sector = ? AND market_cap IS NOT NULL
                ORDER BY market_cap DESC
                LIMIT ?
            """, (sector, limit_per_sector))
            
            stocks = []
            for row in cursor.fetchall():
                r = dict(row)
                stocks.append({
                    "symbol": r["symbol"],
                    "name": r["company_name"],
                    "price": r["price"],
                    "change": r["change_percent"],
                    "marketCap": r["market_cap"],
                    "capCategory": r["market_cap_category"],
                    "volume": r["volume"],
                    "rvol": r["relative_volume"],
                })
            
            if stocks:
                sector_change = sum(s["change"] or 0 for s in stocks) / len(stocks)
                sectors[sector] = {
                    "stocks": stocks,
                    "avgChange": round(sector_change, 2),
                    "stockCount": len(stocks),
                }
        
        return sectors
    
    def get_most_active(self, limit: int = 50) -> list[dict]:
        """Get most active stocks by volume"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM stocks 
            WHERE volume > 0
            ORDER BY volume DESC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_most_volatile(self, limit: int = 50) -> list[dict]:
        """Get most volatile stocks (biggest absolute moves)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT *, ABS(change_percent) as abs_change FROM stocks 
            WHERE volume > 100000
            ORDER BY abs_change DESC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_above_below_sma(self) -> dict:
        """
        Get stocks above/below key moving averages
        Note: This requires SMA data which we'd need to calculate separately
        For now, using 52-week high/low as proxy for trend
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Using proximity to 52w high as bullish indicator
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE distance_from_52w_high >= -20")
        above_50 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE distance_from_52w_high < -20")
        below_50 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE distance_from_52w_high >= -10")
        above_200 = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stocks WHERE distance_from_52w_high < -10")
        below_200 = cursor.fetchone()[0]
        
        total = above_50 + below_50
        
        return {
            "sma50": {
                "above": above_50,
                "below": below_50,
                "above_percent": round((above_50 / total) * 100, 1) if total > 0 else 0,
            },
            "sma200": {
                "above": above_200,
                "below": below_200,
                "above_percent": round((above_200 / total) * 100, 1) if total > 0 else 0,
            },
        }
    
    def get_finviz_style_overview(self) -> dict:
        """Complete Finviz-style market overview"""
        return {
            "breadth": self.get_market_breadth(),
            "sectors": self.get_sector_performance(),
            "sma_analysis": self.get_above_below_sma(),
            "stats": self.get_summary_stats(),
        }

