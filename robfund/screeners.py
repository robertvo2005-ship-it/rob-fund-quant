# -*- coding: utf-8 -*-
"""
Screener chiến lược — port 1:1 luật từ bản JS gốc (bộ chọn "nhà đầu tư huyền thoại").
Chạy trên BCTC thật, không cần mạng, kết quả tất định.
  - Graham Defensive : P/E<=15, P/B<=1.5, Graham№=P/E*P/B<=22.5, cổ tức>0
  - Magic Formula    : xếp hạng Earnings Yield (1/PE) + ROC (ROE proxy)  [bản rút gọn]
  - Piotroski        : lọc theo F-Score đã tính sẵn trong BCTC (>=ngưỡng)
"""
from __future__ import annotations
import pandas as pd


def graham_defensive(f: pd.DataFrame) -> pd.DataFrame:
    """Cổ phiếu phòng thủ kiểu Graham (chỉ áp cho doanh nghiệp phi tài chính)."""
    d = f[f["type"] == "nonfin"].copy()
    d["graham_no"] = d["pe"] * d["pb"]
    ok = (d["pe"] > 0) & (d["pe"] <= 15) & (d["pb"] > 0) & (d["pb"] <= 1.5) \
        & (d["graham_no"] <= 22.5) & (d["divYield"].fillna(0) > 0)
    out = d[ok].sort_values("graham_no")
    return out[["name", "sector", "pe", "pb", "graham_no", "divYield", "roe"]]


def magic_formula(f: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    """Greenblatt Magic Formula (rút gọn): hạng EY + hạng ROC, tổng thấp nhất = tốt."""
    d = f[f["type"] == "nonfin"].copy()
    d["roc"] = d["roe"].fillna(d["roae"])  # bản rút gọn: ROE (fallback ROAE) thay EBIT/Capital
    d = d[(d["pe"] > 0) & d["roc"].notna()]
    d["earnings_yield"] = 1.0 / d["pe"]
    d["rank_ey"] = d["earnings_yield"].rank(ascending=False)
    d["rank_roc"] = d["roc"].rank(ascending=False)
    d["magic_rank"] = d["rank_ey"] + d["rank_roc"]
    out = d.sort_values("magic_rank").head(top)
    return out[["name", "sector", "earnings_yield", "roc", "magic_rank"]]


def piotroski(f: pd.DataFrame, min_score: int = 7) -> pd.DataFrame:
    """Lọc chất lượng theo Piotroski F-Score (đã chấm trong BCTC)."""
    d = f[f["piotroski"].notna()].copy()
    d = d[d["piotroski"] >= min_score]
    out = d.sort_values("piotroski", ascending=False)
    return out[["name", "sector", "piotroski", "piotroskiMax", "roe", "netMargin", "revYoY"]]
