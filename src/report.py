import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    curve = (1 + r).cumprod()
    out = {"Total return": curve.iloc[-1] - 1,
           "Max drawdown": min((curve / curve.cummax() - 1).min(), 0),
           "Best month": r.max(), "Worst month": r.min()}
    if len(r) >= 12:  # annualized numbers are meaningless on a few months
        vol = r.std() * np.sqrt(12)
        out.update({"CAGR": curve.iloc[-1] ** (12 / len(r)) - 1, "Volatility": vol,
                    "Sharpe (rf=0)": r.mean() * 12 / vol})
    return out


def table(cols: dict) -> pd.DataFrame:
    return pd.DataFrame({k: stats(v) for k, v in cols.items()})


def fmt(df):
    out = df.map(lambda x: "" if pd.isna(x) else f"{x:.1%}")
    if "Sharpe (rf=0)" in df.index:
        out.loc["Sharpe (rf=0)"] = df.loc["Sharpe (rf=0)"].map(lambda x: f"{x:.2f}")
    return out


def chart(cols: dict, title, path):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    colors = ["#1f6f8b", "#e09f3e", "#888888", "#9e2a2b"]
    for (name, r), c in zip(cols.items(), colors):
        (1 + r.dropna()).cumprod().plot(ax=ax, label=name, color=c, lw=1.8)
    ax.set_title(title)
    ax.set_ylabel("Growth of $1")
    ax.set_xlabel("")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def letter(cfg, live, weights, path):
    """Pre filled shareholder letter. The numbers are filled in; the thinking is yours."""
    last = live.index[-1]
    m = live.iloc[-1]
    q = live.loc[live.index > last - pd.offsets.MonthEnd(3)]
    itd = (1 + live["fund"]).prod() - 1
    itd_b = (1 + live["benchmark"]).prod() - 1
    holdings = "\n".join(f"| {t} | {cfg.WEIGHTS[t]:.0%} | {weights[t]:.1%} |" for t in cfg.WEIGHTS)
    text = f"""# {cfg.FUND_NAME}: Letter for {last:%B %Y}

## Performance

| | Fund | {cfg.BENCHMARK} |
|---|---|---|
| Month | {m['fund']:.2%} | {m['benchmark']:.2%} |
| Last 3 months | {(1+q['fund']).prod()-1:.2%} | {(1+q['benchmark']).prod()-1:.2%} |
| Since inception ({cfg.INCEPTION}) | {itd:.2%} | {itd_b:.2%} |

Fund value: ${m['value']:,.0f}. Crash guard: {"ON, momentum sleeve moved to core" if m['guard'] else "off"}.

## Holdings

| ETF | Target | Current |
|---|---|---|
{holdings}

## What drove the month
_Which sleeve helped or hurt, and why? Look at MTUM vs VTI for the month._

## Changes and why
_Any rebalance, guard change, or nothing? If nothing, say why you held._

## What I'm watching
_One or two things that could change the strategy: momentum crash risk, rate moves, earnings season._
"""
    path.write_text(text)
