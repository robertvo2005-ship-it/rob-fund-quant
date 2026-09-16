# -*- coding: utf-8 -*-
"""
DEMO "BIG DATA" — quét TOÀN THỊ TRƯỜNG (HOSE/HNX/UPCOM, ~1.500 mã) bằng giá thật,
KÈM bộ lọc thanh khoản (bước data-cleaning then chốt).
  1) Danh sách niêm yết + kéo giá/khối lượng SONG SONG (cache đĩa)
  2) Lọc thanh khoản: ADTV ≥ 1 tỷ/phiên, giá ≥ 5.000đ, bỏ UPCOM
  3) Minervini + Momentum trên vũ trụ ĐÃ LỌC vs CHƯA LỌC
  4) GA backtest walk-forward trên nhóm momentum thanh khoản

Chạy:  python run_bigdata.py            (offline nếu đã có cache trong data/)
        python run_bigdata.py --refresh  (kéo lại toàn sàn, ~90 giây)
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import time
import pandas as pd
from robfund import data, universe, screeners_price as sp, liquidity, backtest, viz

pd.set_option("display.width", 130, "display.max_columns", 20)
REFRESH = "--refresh" in sys.argv
CACHE_PX, CACHE_ADTV = "data/prices_allmarket.csv", "data/adtv_allmarket.csv"


def banner(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def main():
    t0 = time.time()
    banner("1) KÉO DỮ LIỆU TOÀN THỊ TRƯỜNG (giá + khối lượng)")
    if REFRESH or not (pd.io.common.file_exists(CACHE_PX)):
        syms = universe.listed_symbols(("HOSE", "HNX", "UPCOM"))
        print(f"Niêm yết: {len(syms)} mã — đang kéo...")
        px, adtv = data.fetch_market(syms, start="2021-01-01", max_workers=16,
                                     cache_prices=CACHE_PX, cache_adtv=CACHE_ADTV)
    else:
        px, adtv = data.fetch_market([], cache_prices=CACHE_PX, cache_adtv=CACHE_ADTV)
    pts = int(px.notna().to_numpy().sum())
    print(f"→ {px.shape[0]} phiên × {px.shape[1]} mã = {pts:,} điểm giá (~{pts/1e6:.1f} triệu)")

    banner("2) BỘ LỌC THANH KHOẢN (ADTV≥1 tỷ, giá≥5.000đ, bỏ UPCOM)")
    try:
        floors = universe.listed_with_floor()
    except Exception:
        floors = None
    liquid = liquidity.liquid_universe(px, adtv, floors, min_adtv_bn=1.0, min_price=5.0)
    print(f"Trước lọc: {px.shape[1]} mã  →  Sau lọc: {len(liquid)} mã đầu tư được")
    pxl = px[liquid]

    banner("3a) MINERVINI TREND TEMPLATE — trên vũ trụ ĐÃ LỌC (đủ 8/8)")
    passed, _ = sp.minervini_trend(pxl)
    print(f"Số mã đạt 8/8: {len(passed)} — top 12 theo RS:")
    print(passed.head(12).round({"close": 2, "rs_rating": 0, "ret12m": 3}).to_string())

    banner("3b) MOMENTUM 12-1 — top 12 (đã lọc thanh khoản)")
    mom = sp.momentum(pxl, top=12)
    print(mom.round({"close": 2, "mom_12_1": 3, "ret12m": 3, "rs_rating": 0}).to_string())
    # đối chiếu: momentum KHÔNG lọc thường lòi ra micro-cap rác
    mom_raw = sp.momentum(px, top=5)
    print("\n(so sánh) Momentum top 5 khi KHÔNG lọc — thường là micro-cap illiquid:")
    print(mom_raw.round({"close": 2, "mom_12_1": 3, "rs_rating": 0}).to_string())

    banner("4) GA BACKTEST trên nhóm momentum thanh khoản")
    full = pxl.count()
    cand = sp.momentum(pxl, top=40).index
    good = [s for s in cand if full.get(s, 0) >= 0.9 * full.max()][:20]
    px_bt = pxl[good].dropna()
    print(f"Vũ trụ backtest: {len(good)} mã | {px_bt.shape[0]} phiên chung")
    curves = backtest.walk_forward(px_bt, is_win=252, oos_win=63, seed=42, verbose=False)

    banner("5) KẾT QUẢ OUT-OF-SAMPLE: GA (RoB Fund) vs Equal-Weight")
    perf = backtest.performance_table(curves)
    show = perf.copy()
    for c in ["Tổng LN", "CAGR", "Volatility", "Max Drawdown"]:
        show[c] = (perf[c] * 100).round(1).astype(str) + "%"
    show["Sharpe"] = perf["Sharpe"].round(2)
    print(show.to_string())
    (1 + curves).cumprod().round(4).to_csv("outputs_equity_bigdata.csv")
    viz.plot_equity(curves, "RoB Fund (Python) — Backtest OOS: nhóm momentum thanh khoản toàn sàn",
                    "outputs_equity_bigdata.png")

    print(f"\n→ Tổng thời gian: {time.time()-t0:.0f}s | Sản phẩm cũ ở D:\\start up KHÔNG bị đụng.")


if __name__ == "__main__":
    main()
