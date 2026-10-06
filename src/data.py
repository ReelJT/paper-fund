from pathlib import Path
import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"


def load_prices(tickers, start="2012-01-01", refresh=False) -> pd.DataFrame:
    """Daily adjusted closes for the given tickers, cached to data/prices.csv."""
    tickers = sorted(set(tickers))
    if CACHE.exists() and not refresh:
        prices = pd.read_csv(CACHE, index_col=0, parse_dates=True)
        if set(tickers).issubset(prices.columns) and prices.index[-1] >= pd.Timestamp.today().normalize() - pd.Timedelta(days=4):
            return prices[tickers]
    import yfinance as yf
    raw = yf.download(tickers, start=start, auto_adjust=True, progress=False)
    prices = raw["Close"].dropna(how="all")
    CACHE.parent.mkdir(exist_ok=True)
    prices.to_csv(CACHE)
    return prices[tickers]


def synthetic_prices(tickers, start="2012-01-01", end="2027-03-31", seed=3) -> pd.DataFrame:
    """Fake prices for testing offline. Not real data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, end)
    mkt = rng.normal(0.0004, 0.011, len(dates))
    mkt[600:640] -= 0.012          # a fake crash so the guard has something to do
    out = {}
    for t in tickers:
        beta = {"USMV": 0.7, "MTUM": 1.1}.get(t, 1.0)
        out[t] = 100 * np.exp(np.cumsum(beta * mkt + rng.normal(0.00005, 0.004, len(dates))))
    return pd.DataFrame(out, index=dates)
