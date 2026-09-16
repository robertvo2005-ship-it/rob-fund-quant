# -*- coding: utf-8 -*-
"""
DEMO NHANH (chạy tại lớp) — RoB Fund bản Python.
Dùng dữ liệu ĐÃ CACHE trong repo (data/bctc.json + data/prices_demo.csv) nên
CHẠY ĐƯỢC OFFLINE, không cần internet. Thêm cờ --refresh để kéo lại dữ liệu mới.

Chạy:  python run_demo.py            (offline, ~5 giây)
        python run_demo.py --refresh  (kéo giá mới từ VNDIRECT)
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import warnings; warnings.filterwarnings("ignore")
import pandas as pd
from robfund import data, screeners, backtest, viz

pd.set_option("display.width", 120, "display.max_columns", 20)
REFRESH = "--refresh" in sys.argv
CACHE = "data/prices_demo.csv"


def banner(t): print("\n" + "=" * 64 + f"\n{t}\n" + "=" * 64)


def main():
    banner("1) NẠP BCTC (dữ liệu thật, cache trong repo)")
    f = data.load_fundamentals("data/bctc.json")
    print(f"Đã nạp {len(f)} mã VN100 | {len(f.columns)} chỉ tiêu")

    banner("2) SCREENER CHIẾN LƯỢC HUYỀN THOẠI (funda)")
    print("\n[Graham Defensive] P/E≤15, P/B≤1.5, Graham№≤22.5, cổ tức>0:")
    print(screeners.graham_defensive(f).head(10).round(3).to_string())
    print("\n[Magic Formula] top 8 theo hạng EY + ROC:")
    print(screeners.magic_formula(f, top=8).round(4).to_string())
    print("\n[Piotroski F-Score ≥ 7]:")
    pio = screeners.piotroski(f, min_score=7)
    print(pio.head(12).round(3).to_string())

    universe = list(dict.fromkeys(pio.index.tolist()))[:12]
    banner(f"3) GIÁ cho {len(universe)} mã đã sàng lọc ({'ONLINE' if REFRESH else 'từ cache'})")
    px = data.fetch_prices(universe, start="2022-07-01",
                           cache_path=None if REFRESH else CACHE)
    if REFRESH:
        px.to_csv(CACHE)
    px = px.dropna(axis=1)
    print(f"→ {px.shape[0]} phiên × {px.shape[1]} mã ({px.index.min().date()} → {px.index.max().date()})")

    banner("4) GA TỐI ƯU DANH MỤC + BACKTEST WALK-FORWARD")
    curves = backtest.walk_forward(px, is_win=252, oos_win=63, seed=42, verbose=False)

    banner("5) KẾT QUẢ OUT-OF-SAMPLE: GA (RoB Fund) vs Equal-Weight")
    perf = backtest.performance_table(curves)
    show = perf.copy()
    for c in ["Tổng LN", "CAGR", "Volatility", "Max Drawdown"]:
        show[c] = (perf[c] * 100).round(1).astype(str) + "%"
    show["Sharpe"] = perf["Sharpe"].round(2)
    print(show.to_string())
    (1 + curves).cumprod().round(4).to_csv("outputs_equity_demo.csv")
    print("\n→ Lưu đường vốn: outputs_equity_demo.csv")
    viz.plot_equity(curves, "RoB Fund (Python) — Backtest OOS: GA vs Equal-Weight (rổ VN100 chất lượng)",
                    "outputs_equity_demo.png")


if __name__ == "__main__":
    main()
