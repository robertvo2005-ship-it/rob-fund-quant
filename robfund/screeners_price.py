# -*- coding: utf-8 -*-
"""
Screener theo GIÁ — port từ bản JS gốc:
  - Minervini Trend Template : 8 tiêu chí Stage 2 (MA xếp lớp, RS≥70, gần đỉnh 52T...)
  - Momentum (Jegadeesh-Titman): lợi suất 12 tháng, bỏ 1 tháng gần nhất (12-1)
Chạy trên ma trận giá thật (nhiều nghìn mã) → đây là phần "big data" đúng nghĩa.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

LB = 252  # ~52 tuần giao dịch


def compute_price_features(prices: pd.DataFrame) -> pd.DataFrame:
    """Tính đặc trưng kỹ thuật cho TỪNG mã (vector hoá trên toàn bộ ma trận giá)."""
    p = prices.sort_index()
    n = len(p)

    def at(shift_back: int) -> pd.Series:
        return p.iloc[-shift_back] if n > shift_back else pd.Series(np.nan, index=p.columns)

    ma = lambda w: p.rolling(w).mean()
    last = p.iloc[-1]
    feats = pd.DataFrame({
        "close": last,
        "ma50": ma(50).iloc[-1],
        "ma150": ma(150).iloc[-1],
        "ma200": ma(200).iloc[-1],
        "ma200_1m": ma(200).iloc[-22] if n > 222 else pd.Series(np.nan, index=p.columns),
        "hi52": p.rolling(LB).max().iloc[-1],
        "lo52": p.rolling(LB).min().iloc[-1],
        "ret12m": last / at(LB) - 1,          # cho RS rating
        "mom_12_1": at(21) / at(LB) - 1,      # momentum 12-1
    })
    feats["rs_rating"] = feats["ret12m"].rank(pct=True) * 100  # xếp bách phân toàn thị trường
    return feats


def minervini_trend(prices: pd.DataFrame):
    """Trả về (bảng mã đạt đủ 8 tiêu chí, bảng đặc trưng đầy đủ)."""
    d = compute_price_features(prices)
    crit = pd.DataFrame({
        "c1_gia>MA150&200": (d.close > d.ma150) & (d.close > d.ma200),
        "c2_MA150>MA200":   d.ma150 > d.ma200,
        "c3_MA200_doc_len": d.ma200 > d.ma200_1m,
        "c4_MA_xep_lop":    (d.ma50 > d.ma150) & (d.ma150 > d.ma200),
        "c5_gia>MA50":      d.close > d.ma50,
        "c6_tren_day_25%":  d.close >= 1.25 * d.lo52,
        "c7_gan_dinh_25%":  d.close >= 0.75 * d.hi52,
        "c8_RS>=70":        d.rs_rating >= 70,
    })
    d["score"] = crit.sum(axis=1)
    d["pass"] = crit.all(axis=1)
    passed = d[d["pass"]].sort_values("rs_rating", ascending=False)
    return passed[["close", "rs_rating", "ret12m", "score"]], d


def momentum(prices: pd.DataFrame, top: int = 15) -> pd.DataFrame:
    d = compute_price_features(prices)
    d = d[d["mom_12_1"].notna()].sort_values("mom_12_1", ascending=False)
    return d.head(top)[["close", "mom_12_1", "ret12m", "rs_rating"]]
