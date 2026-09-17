# -*- coding: utf-8 -*-
"""
Danh mục đang nắm + đường NAV so với VN-Index và VN100 (equal-weight).
Buy-and-hold từ ngày lập danh mục (inception). Giá trong prices là nghìn đồng → ×1000 = VND.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd


def load_portfolio(path: str = "data/portfolio.json") -> dict:
    return json.load(open(path, encoding="utf-8"))


def load_journal(path: str = "data/journal.csv") -> pd.DataFrame:
    return pd.read_csv(path)


def holdings_table(positions: list[dict], prices: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for p in positions:
        s, sh, cost = p["sym"], p["shares"], p["cost"]
        cur = float(prices[s].dropna().iloc[-1]) * 1000 if s in prices.columns else np.nan
        rows.append(dict(sym=s, shares=sh, cost=cost, price=cur, value=sh * cur,
                         pnl=sh * (cur - cost), pct=(cur / cost - 1) if cost else np.nan))
    return pd.DataFrame(rows).set_index("sym")


def nav_series(positions: list[dict], cash: float, inception, prices: pd.DataFrame) -> pd.Series:
    idx = prices.index[prices.index >= pd.Timestamp(inception)]
    nav = pd.Series(float(cash), index=idx)
    for p in positions:
        s = p["sym"]
        if s in prices.columns:
            nav = nav.add(prices[s].reindex(idx).ffill() * 1000 * p["shares"], fill_value=0)
    return nav


def benchmark_curves(inception, prices: pd.DataFrame, vnindex: pd.Series,
                     vn100_syms: list[str]) -> tuple[pd.Series, pd.Series]:
    """Trả về (VN-Index, VN100 equal-weight) căn theo lịch chung từ inception."""
    idx = prices.index[prices.index >= pd.Timestamp(inception)]
    vni = vnindex.reindex(idx).ffill()
    sub = prices[[s for s in vn100_syms if s in prices.columns]].reindex(idx).ffill().dropna(axis=1)
    ew = (sub / sub.iloc[0]).mean(axis=1)
    return vni, ew


def rebased_100(nav: pd.Series, vni: pd.Series, ew: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({
        "Danh mục (NAV)": nav / nav.iloc[0] * 100,
        "VN-Index": vni / vni.iloc[0] * 100,
        "VN100 (EW)": ew / ew.iloc[0] * 100,
    })
