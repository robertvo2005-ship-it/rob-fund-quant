# -*- coding: utf-8 -*-
"""
Bộ lọc thanh khoản — bước "data cleaning" quan trọng khi quét cả thị trường.
Loại micro-cap illiquid, cổ phiếu giá sàn, và (tuỳ chọn) sàn UPCOM để tránh
kết quả backtest bị bóp méo bởi những mã không đầu tư được ở quy mô thật.
"""
from __future__ import annotations
import pandas as pd


def liquid_universe(prices: pd.DataFrame, adtv: pd.Series, floors: dict | None = None,
                    min_adtv_bn: float = 1.0, min_price: float = 5.0,
                    min_history: int = 300, exclude_upcom: bool = True) -> list[str]:
    """
    Trả về danh sách mã đạt chuẩn thanh khoản:
      - ADTV >= min_adtv_bn (tỷ VND/phiên)
      - giá hiện tại >= min_price (nghìn VND)
      - >= min_history phiên dữ liệu
      - (tuỳ chọn) chỉ HOSE/HNX, bỏ UPCOM
    """
    last = prices.iloc[-1]
    hist = prices.count()
    out = []
    for s in prices.columns:
        if float(adtv.get(s, 0)) < min_adtv_bn:
            continue
        if float(last.get(s, 0)) < min_price:
            continue
        if int(hist.get(s, 0)) < min_history:
            continue
        if exclude_upcom and floors is not None and floors.get(s) not in ("HOSE", "HNX"):
            continue
        out.append(s)
    return out
