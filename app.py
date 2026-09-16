# -*- coding: utf-8 -*-
"""
RoB Fund — Quant Engine (Streamlit web app).
Giao diện web bọc engine Python: screener chiến lược + tối ưu danh mục GA + backtest.
Chạy local:  streamlit run app.py
Deploy:      Streamlit Community Cloud (share.streamlit.io) → link *.streamlit.app
Dữ liệu đọc từ cache trong data/ nên chạy được ngay, không phụ thuộc mạng.
"""
import json
import numpy as np
import pandas as pd
import streamlit as st
from robfund import data, screeners, screeners_price as sp, liquidity, backtest

st.set_page_config(page_title="RoB Fund — Quant Engine", page_icon="📈", layout="wide")


# ------------------------- Nạp dữ liệu (cache) -------------------------
@st.cache_data
def load_fund():
    return data.load_fundamentals("data/bctc.json")


@st.cache_data
def load_market():
    px = pd.read_csv("data/prices_allmarket.csv", index_col=0, parse_dates=True)
    adtv = pd.read_csv("data/adtv_allmarket.csv", index_col=0)["adtv_bn"]
    return px, adtv


@st.cache_data
def load_demo_prices():
    return pd.read_csv("data/prices_demo.csv", index_col=0, parse_dates=True)


@st.cache_data
def load_floors():
    try:
        return json.load(open("data/floors.json", encoding="utf-8"))
    except Exception:
        return None


# ------------------------- Header -------------------------
st.title("📈 RoB Fund — Quant Engine")
st.caption("Screener chiến lược huyền thoại · Tối ưu danh mục bằng thuật toán di truyền (GA) · "
           "Backtest walk-forward — trên dữ liệu thật thị trường chứng khoán Việt Nam.")
st.info("⚠️ Sản phẩm học thuật (môn Applied Big Data in Finance) — **KHÔNG phải khuyến nghị đầu tư**. "
        "Backtest quá khứ không đảm bảo kết quả tương lai.")

tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Screener cơ bản", "📊 Quét toàn thị trường", "🧬 GA Backtest", "ℹ️ Giới thiệu"])

# ------------------------- Tab 1: Fundamental screeners -------------------------
with tab1:
    f = load_fund()
    st.subheader("Bộ chọn chiến lược nhà đầu tư huyền thoại (dữ liệu cơ bản)")
    st.write(f"Rổ **VN100** · {len(f)} mã · nguồn BCTC VNDIRECT.")
    which = st.radio("Chiến lược", ["Graham Defensive", "Magic Formula", "Piotroski F-Score"],
                     horizontal=True)
    if which == "Graham Defensive":
        st.markdown("**Luật:** P/E ≤ 15 · P/B ≤ 1.5 · Graham№ (P/E×P/B) ≤ 22.5 · cổ tức > 0.")
        st.dataframe(screeners.graham_defensive(f).round(3), use_container_width=True)
    elif which == "Magic Formula":
        st.markdown("**Luật:** xếp hạng Earnings Yield (1/PE) + ROC (ROE/ROAE).")
        st.dataframe(screeners.magic_formula(f, top=20).round(4), use_container_width=True)
    else:
        st.markdown("**Luật:** F-Score chất lượng (lợi nhuận, dòng tiền, đòn bẩy, hiệu quả).")
        mn = st.slider("Ngưỡng F-Score tối thiểu", 5, 8, 7)
        st.dataframe(screeners.piotroski(f, min_score=mn).round(3), use_container_width=True)

# ------------------------- Tab 2: Market-wide scan (big data) -------------------------
with tab2:
    px, adtv = load_market()
    floors = load_floors()
    pts = int(px.notna().to_numpy().sum())
    c = st.columns(3)
    c[0].metric("Số mã", f"{px.shape[1]:,}")
    c[1].metric("Số phiên", f"{px.shape[0]:,}")
    c[2].metric("Điểm dữ liệu giá", f"{pts/1e6:.1f} triệu")

    st.subheader("Bộ lọc thanh khoản (data cleaning)")
    cc = st.columns(3)
    min_adtv = cc[0].slider("ADTV tối thiểu (tỷ VND/phiên)", 0.0, 20.0, 1.0, 0.5)
    min_price = cc[1].slider("Giá tối thiểu (nghìn VND)", 0.0, 30.0, 5.0, 1.0)
    excl = cc[2].checkbox("Loại sàn UPCOM", value=True)
    liquid = liquidity.liquid_universe(px, adtv, floors, min_adtv_bn=min_adtv,
                                       min_price=min_price, exclude_upcom=excl)
    st.success(f"Trước lọc: **{px.shape[1]}** mã → Sau lọc: **{len(liquid)}** mã đầu tư được.")
    pxl = px[liquid] if liquid else px

    left, right = st.columns(2)
    with left:
        st.markdown("**🚀 Momentum 12-1 (Jegadeesh–Titman) — top 15**")
        st.dataframe(sp.momentum(pxl, top=15).round(
            {"close": 2, "mom_12_1": 3, "ret12m": 3, "rs_rating": 0}), use_container_width=True)
    with right:
        st.markdown("**📐 Minervini Trend Template (đủ 8/8) — top 15 theo RS**")
        passed, _ = sp.minervini_trend(pxl)
        st.caption(f"{len(passed)} mã đạt đủ 8/8 tiêu chí Stage 2.")
        st.dataframe(passed.head(15).round(
            {"close": 2, "rs_rating": 0, "ret12m": 3}), use_container_width=True)

# ------------------------- Tab 3: GA backtest -------------------------
with tab3:
    st.subheader("Tối ưu danh mục bằng thuật toán di truyền (GA) + backtest walk-forward")
    uni = st.radio("Chọn vũ trụ đầu tư",
                   ["Rổ VN100 chất lượng (Piotroski, demo nhanh)", "Momentum thanh khoản toàn sàn"],
                   horizontal=False)
    seed = st.number_input("Seed (tái lập)", 1, 9999, 42)
    if st.button("▶️ Chạy GA backtest", type="primary"):
        with st.spinner("Đang tối ưu GA qua các kỳ rebalance..."):
            if uni.startswith("Rổ VN100"):
                px_bt = load_demo_prices().dropna(axis=1)
            else:
                px, adtv = load_market()
                floors = load_floors()
                liq = liquidity.liquid_universe(px, adtv, floors, 1.0, 5.0)
                pxl = px[liq]
                full = pxl.count()
                cand = sp.momentum(pxl, top=40).index
                good = [s for s in cand if full.get(s, 0) >= 0.9 * full.max()][:20]
                px_bt = pxl[good].dropna()
            curves = backtest.walk_forward(px_bt, is_win=252, oos_win=63,
                                           seed=int(seed), verbose=False)
            perf = backtest.performance_table(curves)
        st.markdown("**Kết quả out-of-sample**")
        show = perf.copy()
        for col in ["Tổng LN", "CAGR", "Volatility", "Max Drawdown"]:
            show[col] = (perf[col] * 100).round(1).astype(str) + "%"
        show["Sharpe"] = perf["Sharpe"].round(2)
        st.dataframe(show, use_container_width=True)
        st.line_chart((1 + curves).cumprod())
        st.caption(f"Vũ trụ: {px_bt.shape[1]} mã · {px_bt.shape[0]} phiên chung. "
                   "GA tối đa hoá Sharpe in-sample, trần tỷ trọng 20%, shrinkage về equal-weight.")

# ------------------------- Tab 4: About -------------------------
with tab4:
    st.markdown("""
### Về dự án
Bản **Python** của lõi định lượng **RoB Fund** — viết lại từ sản phẩm web gốc (HTML/JS) để làm
project môn **Applied Big Data in Finance**.

**Thành phần:** screener cơ bản (Graham · Magic Formula · Piotroski) + kỹ thuật (Minervini · Momentum),
bộ lọc thanh khoản, tối ưu danh mục bằng **thuật toán di truyền (GA)**, backtest **walk-forward**.

**Dữ liệu:** VNDIRECT (giá/khối lượng, BCTC, danh sách niêm yết) — đã cache trong `data/` để chạy offline.

**Phát hiện chính:** nếu không lọc thanh khoản, momentum "thắng ảo" nhờ micro-cap illiquid (có mã +700%);
bộ lọc thanh khoản là bắt buộc trước khi tin backtest.

**Mã nguồn:** https://github.com/robertvo2005-ship-it/rob-fund-quant

*Sản phẩm RoB Fund gốc được giữ nguyên; repo này chỉ tái tạo engine định lượng bằng Python cho mục đích học thuật.*
""")
