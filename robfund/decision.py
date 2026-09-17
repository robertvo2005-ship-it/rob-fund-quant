# -*- coding: utf-8 -*-
"""
"Quyết định đầu tư" — port trung thực từ bản RoB Fund gốc:
  ① Nhận diện regime thị trường (VN-Index vs MA50/MA200 + biến động)
  ② Xếp hạng factor long-only (trend200 · lowvol · momentum · reversal) bằng z-score
  ③ Điều chỉnh tiền mặt & số vị thế theo regime + IPS
  ④ Phân bổ vốn bằng GA → danh sách MUA cụ thể (KL, số tiền, giá vào, stop, target)
Stop −8%, target R/R 1:3. Đây là HỖ TRỢ QUYẾT ĐỊNH, không phải khuyến nghị.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .optimizer import optimize_ga

# preset theo khung thời gian (nPos, trọng số factor) — bám bản gốc
HORIZON = {
    "short": dict(nPos=3, reb="~2 tuần", tilt="nghiêng ĐỘNG LƯỢNG",
                  W=dict(mom126=2.0, mom252=1.0, lowvol=0.5, rev21=0.0, trend200=1.0)),
    "mid":   dict(nPos=5, reb="hàng THÁNG", tilt="cân bằng factor",
                  W=dict(mom126=1.0, mom252=1.0, lowvol=1.0, rev21=1.0, trend200=1.0)),
    "long":  dict(nPos=8, reb="hàng QUÝ", tilt="nghiêng BIẾN ĐỘNG THẤP / xu hướng",
                  W=dict(mom126=0.5, mom252=0.5, lowvol=2.0, rev21=0.0, trend200=1.5)),
}
STOP_PCT = 8  # cắt lỗ -8%


def market_regime(vnindex: pd.Series) -> dict | None:
    c = vnindex.dropna()
    if len(c) < 210:
        return None
    ma50, ma200 = c.rolling(50).mean(), c.rolling(200).mean()
    if pd.isna(ma200.iloc[-1]) or pd.isna(ma50.iloc[-21]):
        return None
    vol = float(c.pct_change().dropna().iloc[-21:].std() * np.sqrt(252))
    above = c.iloc[-1] > ma200.iloc[-1]
    gold = ma50.iloc[-1] > ma200.iloc[-1]
    slope = ma50.iloc[-1] > ma50.iloc[-21]
    hivol = vol > 0.22
    if above and gold and slope:
        if hivol:
            s = ("up_vol", "Tăng giá · biến động cao", "#d97706",
                 "Xu hướng tăng còn hiệu lực nhưng rung lắc — vào lệnh CHỌN LỌC, siết stop, giảm size.")
        else:
            s = ("up", "Tăng giá · ổn định", "#16a34a",
                 "Thuận lợi triển khai danh mục; có thể nâng tỷ trọng cổ phiếu trong hạn mức IPS.")
    elif (not above) and (not gold):
        s = ("down", "Giảm giá / phòng thủ", "#e11d48",
             "Ưu tiên PHÒNG THỦ: tiền mặt cao, hạn chế mở lệnh mới, tôn trọng stop tuyệt đối.")
    else:
        s = ("side", "Đi ngang / phân hóa", "#64748b",
             "Phần lớn thời gian ĐỨNG NGOÀI — chỉ đánh setup thật rõ, hạ kỳ vọng lợi nhuận.")
    detail = (f"VN-Index {'trên' if above else 'dưới'} MA200 · MA50 {'≥' if gold else '<'} MA200 · "
              f"σ20 ≈ {vol*100:.0f}%/năm {'(cao)' if hivol else '(thấp)'}")
    return dict(state=s[0], label=s[1], color=s[2], stance=s[3], detail=detail, vol=vol)


def _factors(c: pd.Series) -> dict:
    n = len(c)
    r = lambda k: (c.iloc[-1] / c.iloc[-1 - k] - 1) if n > k else np.nan
    vol = c.pct_change().dropna().iloc[-252:].std() * np.sqrt(252)
    sma200 = c.rolling(200).mean().iloc[-1]
    return dict(mom126=r(126), mom252=r(252), lowvol=-float(vol),
                rev21=-(r(21)), trend200=(c.iloc[-1] / sma200 - 1) if pd.notna(sma200) else np.nan)


def factor_rank(prices: pd.DataFrame, universe: list[str], horizon: str = "mid"):
    facs = {s: _factors(prices[s].dropna()) for s in universe if prices[s].dropna().shape[0] >= 260}
    F = pd.DataFrame(facs).T
    z = (F - F.mean()) / F.std(ddof=0).replace(0, np.nan)
    W = HORIZON[horizon]["W"]
    comp = sum(z[f].fillna(0) * W[f] for f in W).sort_values(ascending=False)
    zdisp = pd.DataFrame({"trend200": z["trend200"], "lowvol": z["lowvol"], "mom": z["mom126"]})
    return comp, zdisp


def build_decision(prices: pd.DataFrame, universe: list[str], vnindex: pd.Series,
                   nav: float, base_cash: float = 0.30, horizon: str = "mid", seed: int = 42) -> dict:
    reg = market_regime(vnindex)
    comp, zdisp = factor_rank(prices, universe, horizon)
    max_pos = HORIZON[horizon]["nPos"]
    cash_t, n_pos, convict = base_cash, max_pos, "Trung bình-cao"
    state = reg["state"] if reg else "up"
    if state == "down":
        cash_t, n_pos, convict = 0.85, min(2, max_pos), "Thấp — ưu tiên ĐỨNG NGOÀI"
    elif state == "side":
        cash_t, n_pos, convict = min(0.6, base_cash + 0.2), max(2, max_pos - 1), "Trung bình-thấp"
    elif state == "up_vol":
        cash_t, n_pos, convict = min(0.5, base_cash + 0.1), max_pos, "Trung bình"

    picks = list(comp.index[:n_pos])
    max_w = max(0.25, min(0.35, 1.6 / max_pos))
    R = prices[picks].pct_change().dropna().values[-504:]
    if len(R) >= 20 and len(picks) >= 2:
        w = optimize_ga(R, cap=max_w, shrink=0.5, seed=seed)
    else:
        w = np.full(len(picks), 1.0 / max(1, len(picks)))
    w = w / w.sum() * (1 - cash_t)   # dồn phần còn lại là tiền mặt

    rec = []
    for i, s in enumerate(picks):
        price = round(float(prices[s].dropna().iloc[-1]) * 1000)   # nghìn đồng → VND
        money = w[i] * nav
        shares = max(0, int(money // price // 100) * 100)          # lô 100
        stop = round(price * (1 - STOP_PCT / 100))
        target = round(price + 3 * (price - stop))                 # R/R 1:3
        rec.append(dict(sym=s, weight=float(w[i]), price=price, shares=shares,
                        actual=shares * price, stop=stop, target=target,
                        z=dict(trend200=float(zdisp.loc[s, "trend200"]),
                               lowvol=float(zdisp.loc[s, "lowvol"]),
                               mom=float(zdisp.loc[s, "mom"]))))
    invested = sum(r["actual"] for r in rec)
    return dict(rec=rec, reg=reg, cash_t=cash_t, n_pos=n_pos, max_pos=max_pos, convict=convict,
                nav=nav, invested=invested, n_buy=sum(1 for r in rec if r["shares"] > 0),
                horizon=horizon, reb=HORIZON[horizon]["reb"], scheme="GA · tối ưu Sharpe")
