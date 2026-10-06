"""Simulates the fund month by month.

Weights drift with the market between rebalances, like a real portfolio.
Decisions use only information available at that month end (no lookahead).
"""
import pandas as pd


def crash_signal(bench_daily: pd.Series, threshold: float) -> pd.Series:
    """True at month ends where the benchmark is more than `threshold` below its 12 month high."""
    dd = bench_daily / bench_daily.rolling(252, min_periods=60).max() - 1
    return (dd.resample("ME").last() < -threshold)


def simulate(daily: pd.DataFrame, cfg, start, start_value=100_000, guard=None):
    """Returns (monthly DataFrame with value, return, benchmark, guard flag), holdings log."""
    guard = cfg.CRASH_GUARD if guard is None else guard
    start = pd.Timestamp(start)
    month_ends = daily.resample("ME").last()
    month_ends = month_ends[month_ends.index > start]
    # The fund starts at the close on (or just before) its start date, then marks at each month end
    first_close = daily.loc[:start].iloc[[-1]]
    monthly = pd.concat([first_close, month_ends])
    rets = monthly.pct_change()
    months = monthly.index
    signal = crash_signal(daily[cfg.BENCHMARK], cfg.CRASH_DRAWDOWN)

    def targets(guard_on):
        w = dict(cfg.WEIGHTS)
        if guard_on:
            w[cfg.GUARD_TO] += w.pop(cfg.GUARD_FROM)
        return w

    first = months[0]
    guard_on = bool(guard and signal.asof(first)) if len(signal.loc[:first]) else False
    holdings = {t: start_value * w for t, w in targets(guard_on).items()}
    rows, log = [], [(first, "launch", targets(guard_on))]

    for prev, date in zip(months[:-1], months[1:]):
        before = sum(holdings.values())
        holdings = {t: v * (1 + rets.at[date, t]) for t, v in holdings.items()}
        value = sum(holdings.values())
        rows.append({"date": date, "value": value, "fund": value / before - 1,
                     "benchmark": rets.at[date, cfg.BENCHMARK], "guard": guard_on})

        # Month end decisions, applied from next month on
        new_guard = bool(guard and signal.get(date, False))
        if new_guard != guard_on or date.month in cfg.REBALANCE_MONTHS:
            reason = "guard on" if new_guard and not guard_on else "guard off" if guard_on and not new_guard else "quarterly"
            guard_on = new_guard
            w = targets(guard_on)
            holdings = {t: value * wt for t, wt in w.items()}
            log.append((date, reason, w))

    return pd.DataFrame(rows).set_index("date"), log


def current_weights(daily, cfg, start, start_value):
    """Actual (drifted) weights today."""
    df, log = simulate(daily, cfg, start, start_value)
    last_date, _, w = log[-1]
    since = daily.loc[last_date:].iloc[[0, -1]]
    grown = {t: wt * since[t].iloc[-1] / since[t].iloc[0] for t, wt in w.items()}
    total = sum(grown.values())
    return {t: v / total for t, v in grown.items()}
