import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, Search } from "lucide-react";
import { useMarketNews } from "../hooks/useMarketNews";
import { MiniSparkline } from "../components/MiniSparkline";
import { NewsCard } from "../components/NewsCard";

// Market indices to display with their symbols and labels
const marketIndices = [
    { symbol: "SPY", label: "S&P 500" },
    { symbol: "QQQ", label: "NASDAQ" },
    { symbol: "DIA", label: "DOW" },
    { symbol: "^VIX", label: "VIX" },
    { symbol: "^TNX", label: "10Y Treasury" },
    { symbol: "BTC-USD", label: "Bitcoin" },
];

export function NewsPage() {
    const { data, isLoading, error, refresh } = useMarketNews(15);
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<Array<{ symbol: string; name: string }>>([]);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const navigate = useNavigate();

    // Local list of popular tickers for auto-complete simulation
    // Ideally this would come from an API endpoint like /api/search?q=...
    const POPULAR_TICKERS = [
        { symbol: "AAPL", name: "Apple Inc." },
        { symbol: "ABNB", name: "Airbnb, Inc." },
        { symbol: "ADBE", name: "Adobe Inc." },
        { symbol: "ADI", name: "Analog Devices, Inc." },
        { symbol: "ADP", name: "Automatic Data Processing" },
        { symbol: "ADSK", name: "Autodesk, Inc." },
        { symbol: "AEP", name: "American Electric Power" },
        { symbol: "ALGN", name: "Align Technology" },
        { symbol: "AMAT", name: "Applied Materials" },
        { symbol: "AMD", name: "Advanced Micro Devices" },
        { symbol: "AMGN", name: "Amgen Inc." },
        { symbol: "AMZN", name: "Amazon.com, Inc." },
        { symbol: "ANSS", name: "ANSYS, Inc." },
        { symbol: "ASML", name: "ASML Holding N.V." },
        { symbol: "AVGO", name: "Broadcom Inc." },
        { symbol: "AXP", name: "American Express" },
        { symbol: "BA", name: "Boeing Company" },
        { symbol: "BAC", name: "Bank of America" },
        { symbol: "BABA", name: "Alibaba Group" },
        { symbol: "BKNG", name: "Booking Holdings" },
        { symbol: "BLK", name: "BlackRock, Inc." },
        { symbol: "BMY", name: "Bristol-Myers Squibb" },
        { symbol: "BRK.B", name: "Berkshire Hathaway" },
        { symbol: "BTC-USD", name: "Bitcoin USD" },
        { symbol: "C", name: "Citigroup Inc." },
        { symbol: "CAT", name: "Caterpillar Inc." },
        { symbol: "CHTR", name: "Charter Communications" },
        { symbol: "CMCSA", name: "Comcast Corporation" },
        { symbol: "COST", name: "Costco Wholesale" },
        { symbol: "CRM", name: "Salesforce, Inc." },
        { symbol: "CSCO", name: "Cisco Systems" },
        { symbol: "CSX", name: "CSX Corporation" },
        { symbol: "CTAS", name: "Cintas Corporation" },
        { symbol: "CTSH", name: "Cognizant Technology" },
        { symbol: "CVX", name: "Chevron Corporation" },
        { symbol: "DDOG", name: "Datadog, Inc." },
        { symbol: "DIS", name: "Walt Disney Company" },
        { symbol: "DOW", name: "Dow Inc." },
        { symbol: "EA", name: "Electronic Arts" },
        { symbol: "EBAY", name: "eBay Inc." },
        { symbol: "ETH-USD", name: "Ethereum USD" },
        { symbol: "EXC", name: "Exelon Corporation" },
        { symbol: "FAST", name: "Fastenal Company" },
        { symbol: "FB", name: "Meta Platforms" },
        { symbol: "FISV", name: "Fiserv, Inc." },
        { symbol: "FSLR", name: "First Solar, Inc." },
        { symbol: "GE", name: "General Electric" },
        { symbol: "GILD", name: "Gilead Sciences" },
        { symbol: "GOOG", name: "Alphabet Inc." },
        { symbol: "GOOGL", name: "Alphabet Inc." },
        { symbol: "GS", name: "Goldman Sachs" },
        { symbol: "HD", name: "Home Depot" },
        { symbol: "HON", name: "Honeywell International" },
        { symbol: "IBM", name: "IBM Corporation" },
        { symbol: "IDXX", name: "IDEXX Laboratories" },
        { symbol: "ILMN", name: "Illumina, Inc." },
        { symbol: "INTC", name: "Intel Corporation" },
        { symbol: "INTU", name: "Intuit Inc." },
        { symbol: "ISRG", name: "Intuitive Surgical" },
        { symbol: "JNJ", name: "Johnson & Johnson" },
        { symbol: "JPM", name: "JPMorgan Chase" },
        { symbol: "KDP", name: "Keurig Dr Pepper" },
        { symbol: "KHC", name: "Kraft Heinz" },
        { symbol: "KLAC", name: "KLA Corporation" },
        { symbol: "KO", name: "Coca-Cola Company" },
        { symbol: "LIN", name: "Linde plc" },
        { symbol: "LRCX", name: "Lam Research" },
        { symbol: "LULU", name: "Lululemon Athletica" },
        { symbol: "MA", name: "Mastercard" },
        { symbol: "MAR", name: "Marriott International" },
        { symbol: "MCD", name: "McDonald's" },
        { symbol: "MDLZ", name: "Mondelez International" },
        { symbol: "MELI", name: "MercadoLibre" },
        { symbol: "META", name: "Meta Platforms" },
        { symbol: "MNST", name: "Monster Beverage" },
        { symbol: "MRK", name: "Merck & Co." },
        { symbol: "MRNA", name: "Moderna, Inc." },
        { symbol: "MS", name: "Morgan Stanley" },
        { symbol: "MSFT", name: "Microsoft Corporation" },
        { symbol: "MU", name: "Micron Technology" },
        { symbol: "NFLX", name: "Netflix, Inc." },
        { symbol: "NKE", name: "Nike, Inc." },
        { symbol: "NVDA", name: "NVIDIA Corporation" },
        { symbol: "NXPI", name: "NXP Semiconductors" },
        { symbol: "ODFL", name: "Old Dominion Freight" },
        { symbol: "ORCL", name: "Oracle Corporation" },
        { symbol: "ORXY", name: "O'Reilly Automotive" },
        { symbol: "PANW", name: "Palo Alto Networks" },
        { symbol: "PAYX", name: "Paychex, Inc." },
        { symbol: "PCAR", name: "PACCAR Inc" },
        { symbol: "PEP", name: "PepsiCo, Inc." },
        { symbol: "PFE", name: "Pfizer Inc." },
        { symbol: "PG", name: "Procter & Gamble" },
        { symbol: "PYPL", name: "PayPal Holdings" },
        { symbol: "QCOM", name: "Qualcomm Inc." },
        { symbol: "REGN", name: "Regeneron Pharmaceuticals" },
        { symbol: "ROST", name: "Ross Stores" },
        { symbol: "SBUX", name: "Starbucks" },
        { symbol: "SGEN", name: "Seagen Inc." },
        { symbol: "SIR 1", name: "Sirius XM Holdings" },
        { symbol: "SNPS", name: "Synopsys, Inc." },
        { symbol: "SPY", name: "S&P 500 ETF" },
        { symbol: "SQ", name: "Block, Inc." },
        { symbol: "SWKS", name: "Skyworks Solutions" },
        { symbol: "T", name: "AT&T Inc." },
        { symbol: "TMUS", name: "T-Mobile US" },
        { symbol: "TSLA", name: "Tesla, Inc." },
        { symbol: "TXN", name: "Texas Instruments" },
        { symbol: "UNH", name: "UnitedHealth Group" },
        { symbol: "V", name: "Visa Inc." },
        { symbol: "VRSK", name: "Verisk Analytics" },
        { symbol: "VRSN", name: "VeriSign, Inc." },
        { symbol: "VRTX", name: "Vertex Pharmaceuticals" },
        { symbol: "WBA", name: "Walgreens Boots Alliance" },
        { symbol: "WBD", name: "Warner Bros. Discovery" },
        { symbol: "WDAY", name: "Workday, Inc." },
        { symbol: "WFC", name: "Wells Fargo" },
        { symbol: "WMT", name: "Walmart Inc." },
        { symbol: "XEL", name: "Xcel Energy" },
        { symbol: "XOM", name: "Exxon Mobil" },
        { symbol: "ZM", name: "Zoom Video Communications" },
        { symbol: "ZS", name: "Zscaler, Inc." }
    ];

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setSearchQuery(value);

        if (value.trim()) {
            // Filter suggestion list
            // Matches if symbol starts with value OR name includes value (case insensitive)
            const filtered = POPULAR_TICKERS.filter(ticker =>
                ticker.symbol.toLowerCase().startsWith(value.toLowerCase()) ||
                ticker.name.toLowerCase().includes(value.toLowerCase())
            ).slice(0, 6); // Limit to top 6 results

            setSearchResults(filtered);
            setShowSuggestions(true);
        } else {
            setShowSuggestions(false);
        }
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            navigate(`/chart/${searchQuery.trim().toUpperCase()}`);
            setShowSuggestions(false);
        }
    };

    const handleSuggestionClick = (symbol: string) => {
        setSearchQuery(symbol);
        navigate(`/chart/${symbol.toUpperCase()}`);
        setShowSuggestions(false);
    };

    return (
        <div className="page-container">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="page-title">Today's News</h1>
                    <p className="page-subtitle">Market moving headlines and sentiment</p>
                </div>

                <div className="flex items-center gap-4">
                    <div className="relative">
                        <form onSubmit={handleSearch} className="relative">
                            <input
                                type="text"
                                placeholder="Search..."
                                value={searchQuery}
                                onChange={handleInputChange}
                                onFocus={() => searchQuery.trim() && setShowSuggestions(true)}
                                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                                className="bg-[#1e293b] border border-[#334155] rounded-full py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-accent w-56 transition-all focus:w-64 shadow-sm"
                            />
                            <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                                <Search size={16} />
                            </div>
                        </form>

                        {/* Search Suggestions Dropdown */}
                        {showSuggestions && searchResults.length > 0 && (
                            <div className="absolute right-0 top-full mt-2 w-72 bg-[#1e293b] border border-[#334155] rounded-xl shadow-xl z-50 overflow-hidden">
                                {searchResults.map((result) => (
                                    <button
                                        key={result.symbol}
                                        onClick={() => handleSuggestionClick(result.symbol)}
                                        className="w-full text-left px-4 py-3 hover:bg-white/5 flex items-center justify-between group transition-colors"
                                    >
                                        <div>
                                            <div className="font-bold text-white group-hover:text-accent transition-colors">{result.symbol}</div>
                                            <div className="text-xs text-gray-400">{result.name}</div>
                                        </div>
                                        <div className="text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <Search size={12} />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    <button
                        onClick={refresh}
                        className="p-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                        title="Refresh News"
                    >
                        <RefreshCw size={20} />
                    </button>
                </div>
            </div>

            {/* Market Stats Bar - Now with live mini charts */}
            <div className="market-stats-grid">
                {marketIndices.map((index) => (
                    <MiniSparkline
                        key={index.symbol}
                        symbol={index.symbol}
                        label={index.label}
                        period="1mo"
                        candles={30}
                        width={70}
                        height={35}
                    />
                ))}
            </div>

            {/* Overall Sentiment Indicator if available */}
            {data && (
                <div className="mb-6 p-4 rounded-lg bg-card-bg border border-card-border flex items-center justify-between">
                    <div>
                        <span className="text-gray-400 text-sm">Overall Market Sentiment</span>
                        <div className="text-xl font-bold capitalize" style={{
                            color: data.overall_sentiment === 'positive' ? '#10b981' :
                                data.overall_sentiment === 'negative' ? '#ef4444' : '#9ca3af'
                        }}>
                            {data.overall_sentiment}
                        </div>
                    </div>
                    <div className="text-right">
                        <span className="text-gray-400 text-sm">Articles Analyzed</span>
                        <div className="text-xl font-bold">{data.article_count}</div>
                    </div>
                </div>
            )}

            {/* News Feed */}
            <div className="news-grid">
                {isLoading && !data ? (
                    <div className="col-span-full py-12 text-center text-gray-400">
                        <div className="animate-spin inline-block mb-2">⏳</div> Loading headlines...
                    </div>
                ) : error ? (
                    <div className="col-span-full py-12 text-center text-red-400">
                        Error loading news: {error}
                    </div>
                ) : (
                    data?.articles.map((item) => (
                        <NewsCard key={item.id} news={item} />
                    ))
                )}
            </div>
        </div>
    );
}

export default NewsPage;
