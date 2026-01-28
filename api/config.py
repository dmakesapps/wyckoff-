# api/config.py

"""
API Configuration
"""

import os
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# ═══════════════════════════════════════════════════════════════
# API SETTINGS
# ═══════════════════════════════════════════════════════════════

API_TITLE = "Alpha Discovery API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "High-performance stock data API powered by Alpaca and Yahoo Finance"

# CORS - allow your React frontend
CORS_ORIGINS = [
    "http://localhost:5173",  # Vite default
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

# ═══════════════════════════════════════════════════════════════
# DATA PROVIDER SETTINGS
# ═══════════════════════════════════════════════════════════════

# Alpaca (for real-time stock data)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "PKIYO5HV7CWXVXULBJGUG7BF34")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "3c5V13t1pBziN6PUcRmCMBxw4t65S3HtrRiSi6yNpGVa")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
ALPACA_DATA_URL = "https://data.alpaca.markets"

# ═══════════════════════════════════════════════════════════════
# TECHNICAL INDICATOR SETTINGS
# ═══════════════════════════════════════════════════════════════

# Moving Averages
SMA_PERIODS = [20, 50, 200]
EMA_PERIOD = 20

# RSI
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# MACD
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Bollinger Bands
BB_PERIOD = 20
BB_STD = 2

# Stochastic
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3

# ATR
ATR_PERIOD = 14

# Volume
VOLUME_AVG_PERIOD = 20

# ═══════════════════════════════════════════════════════════════
# ANALYSIS THRESHOLDS
# ═══════════════════════════════════════════════════════════════

# Proximity thresholds (percentage)
ATH_PROXIMITY_THRESHOLD = 5  # Within 5% of ATH
ATL_PROXIMITY_THRESHOLD = 5  # Within 5% of ATL

# Volume thresholds
UNUSUAL_VOLUME_MULTIPLIER = 2.0  # 2x average = unusual

# Options thresholds
UNUSUAL_OPTIONS_VOLUME = 1000  # Minimum volume to flag
PUT_CALL_RATIO_BULLISH = 0.7   # Below this = bullish
PUT_CALL_RATIO_BEARISH = 1.3   # Above this = bearish

