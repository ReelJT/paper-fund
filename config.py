"""The fund's mandate, expressed as settings. Change these, rerun, and everything updates."""

FUND_NAME = "Momentum Core Fund"
INCEPTION = "2026-10-06"        # the day the paper fund "launches"
STARTING_VALUE = 100_000

# Target weights. Each sleeve has a job, based on the factor research:
#   VTI  - core: the whole US market, so the fund never strays far from the benchmark
#   MTUM - momentum tilt: the only factor that sorted stocks correctly in my backtest
#   USMV - drawdown buffer: low vol lagged on return but cut max drawdown (14% vs 24%)
# No reversal sleeve: the backtest found no signal in large caps.
WEIGHTS = {"VTI": 0.60, "MTUM": 0.30, "USMV": 0.10}

BENCHMARK = "SPY"
REBALANCE_MONTHS = (3, 6, 9, 12)   # quarterly, at month end

# Crash guard. My backtest showed momentum crashed in 2021 and 2023, right after
# big selloffs, when beaten down stocks rebounded. Rule: if the benchmark is more
# than CRASH_DRAWDOWN below its 12 month high at month end, move the momentum
# sleeve into the core until it recovers.
CRASH_GUARD = True
CRASH_DRAWDOWN = 0.15
GUARD_FROM = "MTUM"
GUARD_TO = "VTI"

BACKTEST_START = "2013-06-01"   # MTUM launched April 2013
