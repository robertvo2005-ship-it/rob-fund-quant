# -*- coding: utf-8 -*-
"""
RoB Fund — Quant Engine (Streamlit web app, giao diện phối theo bản gốc RoB Fund).
Chạy local:  streamlit run app.py
Deploy:      Streamlit Community Cloud → link *.streamlit.app
Dữ liệu đọc từ cache trong data/ nên chạy được ngay, không phụ thuộc mạng.
"""
import json
import pandas as pd
import streamlit as st
from robfund import data, screeners, screeners_price as sp, liquidity, backtest

st.set_page_config(page_title="RoB Fund — Quant Engine", page_icon="📈", layout="wide")

# ------------------------- Giao diện (phối theo RoB Fund gốc) -------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{ --blue:#2f6bff; --blue-d:#1e50d6; --red:#e5484d; --green:#16a34a;
       --ink:#0f172a; --muted:#64748b; --card:#f6f7f9; --border:#e6e8ee; }
html, body, [class*="css"]{ font-family:'Inter',system-ui,sans-serif; }
.block-container{ padding-top:1.2rem; max-width:1200px; }
#MainMenu, footer{ visibility:hidden; }

/* Header banner */
.rf-head{ display:flex; justify-content:space-between; align-items:center;
  border:1px solid var(--border); border-radius:16px; padding:16px 22px;
  background:linear-gradient(180deg,#fff,#fbfcff); margin-bottom:14px; }
.rf-title{ font-size:26px; font-weight:800; color:var(--ink); letter-spacing:-.3px; }
.rf-title span{ color:var(--blue); }
.rf-badge{ background:#fdecec; color:var(--red); font-size:11px; font-weight:700;
  padding:3px 9px; border-radius:20px; margin-left:8px; vertical-align:middle;
  border:1px solid #f6c6c6; }
.rf-sub{ color:var(--muted); font-size:13.5px; margin-top:4px; }
.rf-menu{ border:1px solid var(--border); border-radius:10px; padding:8px 14px;
  color:var(--ink); font-weight:600; font-size:13px; background:#fff; white-space:nowrap; }

/* Stat cards */
.rf-cards{ display:flex; gap:12px; margin:6px 0 10px; flex-wrap:wrap; }
.rf-card{ flex:1; min-width:150px; background:var(--card); border:1px solid var(--border);
  border-radius:14px; padding:14px 16px; }
.rf-card .lbl{ font-size:11px; font-weight:700; color:var(--muted);
  text-transform:uppercase; letter-spacing:.4px; }
.rf-card .val{ font-size:24px; font-weight:800; color:var(--ink); margin-top:2px; }
.rf-card .val.blue{ color:var(--blue); } .rf-card .val.green{ color:var(--green); }
.rf-card .sub{ font-size:11.5px; color:var(--muted); margin-top:2px; }

/* Tabs -> pill kiểu RoB Fund */
.stTabs [data-baseweb="tab-list"]{ gap:8px; border-bottom:none; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none; }
.stTabs [data-baseweb="tab"]{ background:var(--blue); color:#fff !important; border-radius:10px;
  padding:9px 18px; font-weight:600; font-size:14px; }
.stTabs [data-baseweb="tab"] p{ color:#fff !important; font-weight:600; }
.stTabs [aria-selected="true"]{ background:var(--red) !important; }

/* Buttons */
.stButton>button{ background:var(--blue); color:#fff; border:none; border-radius:10px;
  font-weight:700; padding:8px 18px; }
.stButton>button:hover{ background:var(--blue-d); color:#fff; }

/* Dataframe header */
[data-testid="stDataFrame"] thead th{ background:#f1f4fa; color:var(--muted);
  text-transform:uppercase; font-size:11px; letter-spacing:.3px; }
h2,h3{ color:var(--ink); font-weight:700; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def header():
    st.markdown(
        '<div class="rf-head"><div>'
        '<div class="rf-title">RoB <span>Fund</span> · Quant Engine'
        '<span class="rf-badge">BẢN HỌC THUẬT</span></div>'
        '<div class="rf-sub">Screener chiến lược huyền thoại · Tối ưu danh mục bằng thuật toán '
        'di truyền (GA) · Backtest walk-forward — dữ liệu thật TTCK Việt Nam</div>'
        '</div><div class="rf-menu">☰ Applied Big Data in Finance</div></div>',
        unsafe_allow_html=True)


def cards(items):
    html = '<div class="rf-cards">'
    for lbl, val, sub, cls in items:
        html += (f'<div class="rf-card"><div class="lbl">{lbl}</div>'
                 f'<div class="val {cls}">{val}</div><div class="sub">{sub}</div></div>')
    st.markdown(html + '</div>', unsafe_allow_html=True)


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


# ------------------------- Trang -------------------------
header()
st.markdown('<div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:12px;'
            'padding:10px 14px;font-size:13px;color:#9a3412;margin-bottom:12px;">'
            '⚠️ Sản phẩm học thuật — <b>KHÔNG phải khuyến nghị đầu tư</b>. '
            'Backtest quá khứ không đảm bảo kết quả tương lai.</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🏆 Chiến lược", "📊 Quét thị trường", "🧬 GA Backtest", "ℹ️ Giới thiệu"])

# ---- Tab 1 ----
with tab1:
    f = load_fund()
    cards([
        ("Rổ cổ phiếu", f"{len(f)}", "mã VN100", ""),
        ("Nguồn dữ liệu", "VNDIRECT", "BCTC & tỷ số", "blue"),
        ("Chiến lược", "3", "Graham · Magic · Piotroski", ""),
    ])
    st.subheader("Bộ chọn chiến lược nhà đầu tư huyền thoại")
    which = st.radio("Chiến lược", ["Graham Defensive", "Magic Formula", "Piotroski F-Score"],
                     horizontal=True, label_visibility="collapsed")
    if which == "Graham Defensive":
        st.caption("Luật: P/E ≤ 15 · P/B ≤ 1.5 · Graham№ (P/E×P/B) ≤ 22.5 · cổ tức > 0.")
        st.dataframe(screeners.graham_defensive(f).round(3), use_container_width=True)
    elif which == "Magic Formula":
        st.caption("Luật: xếp hạng Earnings Yield (1/PE) + ROC (ROE/ROAE).")
        st.dataframe(screeners.magic_formula(f, top=20).round(4), use_container_width=True)
    else:
        st.caption("Luật: F-Score chất lượng (lợi nhuận, dòng tiền, đòn bẩy, hiệu quả).")
        mn = st.slider("Ngưỡng F-Score tối thiểu", 5, 8, 7)
        st.dataframe(screeners.piotroski(f, min_score=mn).round(3), use_container_width=True)

# ---- Tab 2 ----
with tab2:
    px, adtv = load_market()
    floors = load_floors()
    pts = int(px.notna().to_numpy().sum())
    cards([
        ("Số mã", f"{px.shape[1]:,}", "toàn HOSE/HNX/UPCOM", ""),
        ("Số phiên", f"{px.shape[0]:,}", "~4 năm", ""),
        ("Điểm dữ liệu giá", f"{pts/1e6:.1f} triệu", "big data", "blue"),
    ])
    st.subheader("Bộ lọc thanh khoản (data cleaning)")
    cc = st.columns(3)
    min_adtv = cc[0].slider("ADTV tối thiểu (tỷ VND/phiên)", 0.0, 20.0, 1.0, 0.5)
    min_price = cc[1].slider("Giá tối thiểu (nghìn VND)", 0.0, 30.0, 5.0, 1.0)
    excl = cc[2].checkbox("Loại sàn UPCOM", value=True)
    liquid = liquidity.liquid_universe(px, adtv, floors, min_adtv_bn=min_adtv,
                                       min_price=min_price, exclude_upcom=excl)
    cards([("Trước lọc", f"{px.shape[1]}", "toàn thị trường", ""),
           ("Sau lọc", f"{len(liquid)}", "mã đầu tư được", "green")])
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

# ---- Tab 3 ----
with tab3:
    st.subheader("Tối ưu danh mục bằng thuật toán di truyền (GA) + backtest walk-forward")
    uni = st.radio("Vũ trụ đầu tư",
                   ["Rổ VN100 chất lượng (Piotroski, demo nhanh)", "Momentum thanh khoản toàn sàn"])
    seed = st.number_input("Seed (tái lập)", 1, 9999, 42)
    if st.button("▶ Chạy GA backtest & ra kết quả"):
        with st.spinner("Đang tối ưu GA qua các kỳ rebalance..."):
            if uni.startswith("Rổ VN100"):
                px_bt = load_demo_prices().dropna(axis=1)
            else:
                px, adtv = load_market()
                liq = liquidity.liquid_universe(px, adtv, load_floors(), 1.0, 5.0)
                pxl = px[liq]
                full = pxl.count()
                cand = sp.momentum(pxl, top=40).index
                good = [s for s in cand if full.get(s, 0) >= 0.9 * full.max()][:20]
                px_bt = pxl[good].dropna()
            curves = backtest.walk_forward(px_bt, is_win=252, oos_win=63,
                                           seed=int(seed), verbose=False)
            perf = backtest.performance_table(curves)
        ga = perf.loc["GA (RoB Fund)"]
        cards([
            ("GA — Tổng LN", f"{ga['Tổng LN']*100:.0f}%", "out-of-sample", "green"),
            ("GA — Sharpe", f"{ga['Sharpe']:.2f}", "so với EW", "blue"),
            ("GA — Max Drawdown", f"{ga['Max Drawdown']*100:.0f}%", "sụt giảm sâu nhất", ""),
        ])
        show = perf.copy()
        for col in ["Tổng LN", "CAGR", "Volatility", "Max Drawdown"]:
            show[col] = (perf[col] * 100).round(1).astype(str) + "%"
        show["Sharpe"] = perf["Sharpe"].round(2)
        st.dataframe(show, use_container_width=True)
        st.line_chart((1 + curves).cumprod())
        st.caption(f"Vũ trụ: {px_bt.shape[1]} mã · {px_bt.shape[0]} phiên chung. "
                   "GA tối đa hoá Sharpe in-sample, trần tỷ trọng 20%, shrinkage về equal-weight.")

# ---- Tab 4 ----
with tab4:
    st.markdown("""
### Về dự án
Bản **Python** của lõi định lượng **RoB Fund** — viết lại từ sản phẩm web gốc (HTML/JS) để làm
project môn **Applied Big Data in Finance**.

**Thành phần:** screener cơ bản (Graham · Magic Formula · Piotroski) + kỹ thuật (Minervini · Momentum),
bộ lọc thanh khoản, tối ưu danh mục bằng **thuật toán di truyền (GA)**, backtest **walk-forward**.

**Dữ liệu:** VNDIRECT — đã cache trong `data/` để chạy offline.

**Phát hiện chính:** nếu không lọc thanh khoản, momentum "thắng ảo" nhờ micro-cap illiquid (có mã +700%);
bộ lọc thanh khoản là bắt buộc trước khi tin backtest.

**Mã nguồn:** https://github.com/robertvo2005-ship-it/rob-fund-quant

*Giao diện phối theo sản phẩm RoB Fund gốc; đây là bản engine định lượng bằng Python cho mục đích học thuật.*
""")
