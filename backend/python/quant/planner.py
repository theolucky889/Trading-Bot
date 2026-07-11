"""Investment plan builder (monthly DCA planner).

User picks a monthly budget, a time span in months, and stock sectors.
The planner:
  1. allocates the budget — equal weight per sector, equal weight per ticker
     inside a sector (simple and explainable; no return-chasing optimization),
  2. simulates that DCA plan over the PAST `months` months on real prices
     (buys at the first trading close of each month),
  3. compares it against putting the same monthly budget into a benchmark
     (0050 by default), and
  4. projects the future value range from historical monthly return/volatility.

Historical simulation is evidence, not a promise — the API response carries a
disclaimer and per-source warnings, and the frontend must show them.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from .data import PriceSeries, get_price_series

SECTORS: Dict[str, dict] = {
    "tw_semiconductors": {
        "label": "Taiwan Semiconductors",
        "market": "TW",
        "tickers": {"2330": "TSMC", "2303": "UMC", "2454": "MediaTek"},
    },
    "tw_financials": {
        "label": "Taiwan Financials",
        "market": "TW",
        "tickers": {"2881": "Fubon FHC", "2882": "Cathay FHC", "2891": "CTBC FHC"},
    },
    "tw_electronics": {
        "label": "Taiwan Electronics Hardware",
        "market": "TW",
        "tickers": {"2317": "Hon Hai (Foxconn)", "2382": "Quanta", "2357": "ASUS"},
    },
    "tw_telecom": {
        "label": "Taiwan Telecom",
        "market": "TW",
        "tickers": {"2412": "Chunghwa Telecom", "3045": "Taiwan Mobile"},
    },
    "tw_shipping": {
        "label": "Taiwan Shipping",
        "market": "TW",
        "tickers": {"2603": "Evergreen Marine", "2609": "Yang Ming"},
    },
    "tw_etf": {
        "label": "Taiwan ETFs",
        "market": "TW",
        "tickers": {"0050": "Yuanta Taiwan 50", "0056": "Yuanta High Dividend"},
    },
    "us_tech": {
        "label": "US Technology",
        "market": "US",
        "tickers": {"AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "GOOGL": "Alphabet"},
    },
    "us_consumer": {
        "label": "US Consumer",
        "market": "US",
        "tickers": {"AMZN": "Amazon", "TSLA": "Tesla", "MCD": "McDonald's"},
    },
    "crypto": {
        "label": "Crypto (high risk)",
        "market": "CRYPTO",
        "tickers": {"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum"},
    },
}

DISCLAIMER = (
    "Historical simulation, not investment advice. Past performance does not "
    "guarantee future results; projections assume history repeats, which it may not."
)


def sector_catalog() -> List[dict]:
    return [
        {
            "id": sid,
            "label": meta["label"],
            "market": meta["market"],
            "tickers": [{"symbol": s, "name": n} for s, n in meta["tickers"].items()],
        }
        for sid, meta in SECTORS.items()
    ]


def _monthly_first_closes(series: PriceSeries) -> Dict[str, float]:
    """Map 'YYYY-MM' -> close of the first trading day of that month."""
    out: Dict[str, float] = {}
    for c in series.candles:
        key = c.date[:7]
        if key not in out:
            out[key] = c.close
    return out


def build_plan(
    monthly_budget: float,
    months: int,
    sectors: List[str],
    benchmark: str = "0050",
) -> dict:
    unknown = [s for s in sectors if s not in SECTORS]
    if unknown:
        raise ValueError(f"Unknown sectors: {', '.join(unknown)}. Available: {', '.join(SECTORS)}")
    if not sectors:
        raise ValueError("Select at least one sector")

    # ── allocation: equal by sector, equal by ticker within sector ──
    allocation: List[dict] = []
    sector_weight = 1.0 / len(sectors)
    for sid in sectors:
        meta = SECTORS[sid]
        per_ticker = sector_weight / len(meta["tickers"])
        for sym, name in meta["tickers"].items():
            allocation.append(
                {
                    "symbol": sym,
                    "name": name,
                    "sector": sid,
                    "sector_label": meta["label"],
                    "weight": round(per_ticker, 6),
                    "monthly_amount": round(monthly_budget * per_ticker, 2),
                }
            )

    # ── fetch history for every holding + benchmark ──
    days = months * 31 + 40
    warnings: List[str] = []
    monthly: Dict[str, Dict[str, float]] = {}
    for item in allocation:
        series = get_price_series(item["symbol"], days)
        if series.warning:
            warnings.append(f"{item['symbol']}: {series.warning}")
        monthly[item["symbol"]] = _monthly_first_closes(series)

    bench_symbol = benchmark.strip().upper()
    bench_series = get_price_series(bench_symbol, days)
    if bench_series.warning:
        warnings.append(f"{bench_symbol} (benchmark): {bench_series.warning}")
    bench_monthly = _monthly_first_closes(bench_series)

    # months available for EVERY holding and the benchmark
    common = set(bench_monthly)
    for m in monthly.values():
        common &= set(m)
    month_keys = sorted(common)[-months:]
    if len(month_keys) < 2:
        raise ValueError("Not enough overlapping price history to simulate this plan")
    if len(month_keys) < months:
        warnings.append(
            f"Only {len(month_keys)} of {months} months have overlapping history; simulation shortened."
        )

    # ── DCA simulation ──
    shares: Dict[str, float] = {item["symbol"]: 0.0 for item in allocation}
    bench_shares = 0.0
    invested_track: List[float] = []
    value_track: List[float] = []
    bench_track: List[float] = []
    invested = 0.0
    for mk in month_keys:
        invested += monthly_budget
        for item in allocation:
            price = monthly[item["symbol"]][mk]
            if price > 0:
                shares[item["symbol"]] += (monthly_budget * item["weight"]) / price
        bench_price = bench_monthly[mk]
        if bench_price > 0:
            bench_shares += monthly_budget / bench_price
        value_track.append(
            round(sum(shares[s] * monthly[s][mk] for s in shares), 2)
        )
        bench_track.append(round(bench_shares * bench_price, 2))
        invested_track.append(round(invested, 2))

    final_value = value_track[-1]
    bench_final = bench_track[-1]
    for item in allocation:
        last_price = monthly[item["symbol"]][month_keys[-1]]
        item["shares"] = round(shares[item["symbol"]], 4)
        item["final_value"] = round(shares[item["symbol"]] * last_price, 2)

    # ── projection from historical monthly portfolio returns ──
    port_rets: List[float] = []
    for i in range(1, len(month_keys)):
        prev_k, cur_k = month_keys[i - 1], month_keys[i]
        r = sum(
            item["weight"] * (monthly[item["symbol"]][cur_k] / monthly[item["symbol"]][prev_k] - 1)
            for item in allocation
            if monthly[item["symbol"]][prev_k] > 0
        )
        port_rets.append(r)
    mu = sum(port_rets) / len(port_rets)
    var = (
        sum((r - mu) ** 2 for r in port_rets) / (len(port_rets) - 1)
        if len(port_rets) > 1
        else 0.0
    )
    sigma = math.sqrt(var)

    def _fv(monthly_return: float, n: int) -> float:
        """Future value of `n` monthly contributions growing at monthly_return."""
        if abs(monthly_return) < 1e-9:
            return monthly_budget * n
        g = 1 + monthly_return
        return monthly_budget * g * (g**n - 1) / (g - 1)

    projection = {
        "months": months,
        "expected_monthly_return": round(mu, 4),
        "monthly_volatility": round(sigma, 4),
        "invested": round(monthly_budget * months, 2),
        "expected": round(_fv(mu, months), 2),
        "optimistic": round(_fv(mu + sigma, months), 2),
        "pessimistic": round(_fv(max(mu - sigma, -0.5), months), 2),
        "note": "Bands are +/-1 std dev of historical monthly returns compounded forward - a rough range, not a forecast.",
    }

    return {
        "monthly_budget": monthly_budget,
        "months": months,
        "sectors": sectors,
        "benchmark": bench_symbol,
        "warnings": warnings,
        "allocation": allocation,
        "simulation": {
            "month_labels": month_keys,
            "invested": invested_track,
            "portfolio_value": value_track,
            "benchmark_value": bench_track,
            "summary": {
                "months_simulated": len(month_keys),
                "invested": round(invested, 2),
                "final_value": final_value,
                "total_return": round(final_value / invested - 1, 4) if invested else 0.0,
                "benchmark_final_value": bench_final,
                "benchmark_return": round(bench_final / invested - 1, 4) if invested else 0.0,
            },
        },
        "projection": projection,
        "disclaimer": DISCLAIMER,
    }
