# Backend Feature Request: Market Pulse API

## **Objective**
Create a new API endpoint that returns bite-sized, AI-generated financial updates across multiple categories. This will power the "What's happening today" section on the home page.

## **Why This Is Needed**
The current news headlines are too long and generic. We need short, punchy updates that summarize:
- Real-time market data
- Key price movements
- Important financial events

**Example Output (what we want):**
```
Markets: S&P 500 rallies 1.2% on strong tech earnings
Crypto: Bitcoin holds above $105K amid ETF inflows
Economy: Fed officials signal patience on rate cuts
Earnings: NVDA beats estimates, guides higher on AI demand
Tech: Apple announces $110B buyback, stock hits ATH
Commodities: Gold steady near $2,100 as dollar weakens
```

## **Proposed Endpoint**

### `GET /api/market/pulse`

**Response Schema:**
```json
{
  "generated_at": "2026-01-25T14:30:00Z",
  "updates": [
    {
      "category": "Markets",
      "headline": "S&P 500 rallies 1.2% on strong tech earnings",
      "sentiment": "positive"
    },
    {
      "category": "Crypto", 
      "headline": "Bitcoin holds above $105K amid ETF inflows",
      "sentiment": "positive"
    },
    {
      "category": "Economy",
      "headline": "Fed officials signal patience on rate cuts",
      "sentiment": "neutral"
    },
    {
      "category": "Earnings",
      "headline": "NVDA beats estimates, guides higher on AI demand",
      "sentiment": "positive"
    },
    {
      "category": "Tech",
      "headline": "Apple announces $110B buyback, stock hits ATH",
      "sentiment": "positive"
    },
    {
      "category": "Commodities",
      "headline": "Gold steady near $2,100 as dollar weakens",
      "sentiment": "neutral"
    }
  ],
  "cache_expires_at": "2026-01-25T14:45:00Z"
}
```

## **Implementation Guide**

### Step 1: Gather Real-Time Data
Fetch the following data points:
- **Markets:** S&P 500, NASDAQ, Dow Jones current price & daily change %
- **Crypto:** Bitcoin & Ethereum price & 24h change
- **Economy:** Latest Fed news, treasury yields, economic indicators
- **Earnings:** Any companies reporting today or recently (use existing news data)
- **Tech:** Top tech stock movers or breaking tech news
- **Commodities:** Gold, Oil prices & daily change

### Step 2: Generate Headlines with Kimi
Use Kimi to synthesize this data into one-sentence updates per category.

**Prompt Template:**
```
You are a financial news editor. Generate ONE concise headline (max 60 characters) for each category based on the provided market data. 

Rules:
- No periods at the end
- Use specific numbers when available (e.g., "up 1.2%", "$105K")
- Be informative, not clickbait
- Capture the day's key theme for each category

Data:
{market_data_json}

Output format (JSON):
[
  {"category": "Markets", "headline": "...", "sentiment": "positive|negative|neutral"},
  ...
]
```

### Step 3: Caching
Cache the response for 15 minutes to avoid excessive API calls. Include `cache_expires_at` in the response so the frontend knows when to refresh.

## **Frontend Integration**
Once this endpoint exists, the frontend `MarketFeed.tsx` will call `/api/market/pulse` instead of `/api/market/news` and display the returned `updates` array.

## **Categories to Support**
Required:
1. **Markets** - Major indices (S&P, NASDAQ, Dow)
2. **Crypto** - Bitcoin, Ethereum
3. **Economy** - Fed, rates, economic data
4. **Earnings** - Notable earnings reports
5. **Tech** - Big tech moves
6. **Commodities** - Gold, Oil

Optional additions:
7. **Sectors** - Best/worst performing sector
8. **Currencies** - USD strength, major pairs
