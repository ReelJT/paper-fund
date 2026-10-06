"""Paper fund tracker.

    python run.py            # backtest of the strategy + live results since inception
    python run.py --refresh  # re-download prices
    python run.py --demo     # fake data, no internet
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
import pandas as pd

import config as cfg
from data import load_prices, synthetic_prices
from fund import simulate, current_weights
from report import table, fmt, chart, letter

OUT = Path(__file__).parent / "output"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--demo", action="store_true")
    a = p.parse_args()
    OUT.mkdir(exist_ok=True)
    pd.options.display.width = 200

    tickers = list(cfg.WEIGHTS) + [cfg.BENCHMARK]
    daily = synthetic_prices(tickers) if a.demo else load_prices(tickers, refresh=a.refresh)
    daily = daily.dropna()

    # 1. Historical backtest: the same rules applied to the past
    with_guard, log = simulate(daily, cfg, cfg.BACKTEST_START, guard=True)
    no_guard, _ = simulate(daily, cfg, cfg.BACKTEST_START, guard=False)
    vti_only = daily["VTI"].resample("ME").last().pct_change().reindex(with_guard.index)
    cols = {"Fund (with crash guard)": with_guard["fund"], "Fund (no guard)": no_guard["fund"],
            "100% VTI": vti_only, cfg.BENCHMARK: with_guard["benchmark"]}
    print(f"\n=== Backtest {with_guard.index[0]:%Y-%m} to {with_guard.index[-1]:%Y-%m} (hypothetical) ===")
    bt = table(cols)
    print(fmt(bt))
    bt.to_csv(OUT / "backtest_summary.csv")
    with_guard.to_csv(OUT / "backtest_monthly.csv")
    chart(cols, f"{cfg.FUND_NAME}: backtest", OUT / "backtest.png")
    guard_months = int(with_guard["guard"].sum())
    print(f"\nCrash guard was on in {guard_months} of {len(with_guard)} months.")
    yearly = (1 + with_guard[["fund", "benchmark"]]).groupby(with_guard.index.year).prod() - 1
    yearly["no_guard"] = (1 + no_guard["fund"]).groupby(no_guard.index.year).prod() - 1
    print("\nCalendar year returns:")
    print(yearly.map(lambda x: f"{x:.1%}"))

    # 2. Live paper fund since inception
    inception = pd.Timestamp(cfg.INCEPTION)
    print(f"\n=== Live since inception {inception:%Y-%m-%d} ===")
    if daily.index[-1] < inception + pd.offsets.MonthEnd(1):
        print("No completed month yet. Rerun after the first month end.")
        w = cfg.WEIGHTS
    else:
        live, live_log = simulate(daily, cfg, cfg.INCEPTION, cfg.STARTING_VALUE)
        live.to_csv(OUT / "live_monthly.csv")
        print(fmt(table({"Fund": live["fund"], cfg.BENCHMARK: live["benchmark"]})))
        w = current_weights(daily, cfg, cfg.INCEPTION, cfg.STARTING_VALUE)
        path = OUT / f"letter_{live.index[-1]:%Y-%m}.md"
        letter(cfg, live, w, path)
        print(f"\nDraft letter written to {path.name}")
        for d, why, wt in live_log:
            print(f"  {d:%Y-%m-%d} {why}: " + ", ".join(f"{t} {x:.0%}" for t, x in wt.items()))
    print("\nCurrent weights: " + ", ".join(f"{t} {x:.1%}" for t, x in w.items()))
    print(f"Saved to {OUT}/")


if __name__ == "__main__":
    main()
