# Backend Fix: Accurate Period Returns

## **Objective**
Fix inaccurate percentage change calculations for chart periods (5D, 1M, etc.) by providing the **Previous Close** price in the chart API response.

## **The Issue**
Currently, the frontend calculates percentage change as:
`((Last Close - First Open) / First Open) * 100`

This methodology is incorrect for standard financial "Period Return" calculations because it ignores the price gap (overnight/weekend) *before* the period started.

*   **Example:** A "5 Day Change" should compare **Now** vs **Close of 6th day ago**.
*   **Current Behavior:** Compares **Now** vs **Open of 5th day ago**.

## **Required Backend Changes**

Please update the `GET /api/chart/{symbol}` endpoint in `main.py` (or relevant router) to include a `previousClose` field.

### **1. Query Logic Update**
When fetching historical data for a requested `period` (e.g., `5d`), the query needs to look back one extra trading day to find the true "base price" for the calculation.

*   **If requesting `N` days:** Fetch `N + 1` days of history.
*   **Identify Base Value:** The `close` price of the *oldest* extra record is the `periodPreviousClose`.
*   **Return Data:** Return only the requested `N` records in the `candlestick` array, but use the extra record to populate the metadata.

### **2. Response Schema Update**
Add `periodPreviousClose` to the `meta` object in the JSON response.

**Target JSON Structure:**
```json
{
  "symbol": "AAPL",
  "interval": "1d",
  "candlestick": [
    // ... Returns only the requested candles (e.g., 5 days) ...
    { "time": "2023-10-23", "open": 170.00, "close": 173.00, ... },
    { "time": "2023-10-24", "open": 173.50, "close": 175.00, ... }
  ],
  "meta": {
    "lastPrice": 175.00,
    "lastDate": "2023-10-24",
    "periodPreviousClose": 168.50  // <--- NEW FIELD: Closing price of the day BEFORE the first candle
  }
}
```

## **Implementation Steps for Cursor/Developer**

1.  **Locate the endpoint** handling `GET /api/chart/{symbol}`.
2.  **Modify the database query** to fetch `start_date - 1 trading day` (or simply fetch one extra record earlier than the requested limit).
3.  **Extract the close price** from that preceding record.
4.  **Inject it** into the response model under `meta`.
