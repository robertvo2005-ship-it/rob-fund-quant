# -*- coding: utf-8 -*-
"""
RoB Fund — Quant Engine (Streamlit web app).
Giao diện bám sát bản gốc RoB Fund: nền #f4f7fc, Segoe UI, thẻ KPI trắng-viền-bóng,
bảng HTML tự dựng (mã in đậm + chip ngành, số màu xanh/đỏ).
Chạy local:  streamlit run app.py     |     Deploy: Streamlit Community Cloud
"""
import json
import pandas as pd
import streamlit as st
from robfund import data, screeners, screeners_price as sp, liquidity, backtest

st.set_page_config(page_title="RoB Fund — Quant Engine", page_icon="📈", layout="wide")

# =========================== GIAO DIỆN (tokens từ bản gốc) ===========================
CSS = """
<style>
.stApp{ background:#f4f7fc; }
html, body, [class*="css"], .stMarkdown, p, div, span, label{
  font-family:'Segoe UI',system-ui,-apple-system,'Roboto',sans-serif; color:#0f172a; }
.block-container{ padding-top:1rem; padding-bottom:2rem; max-width:1180px; }
#MainMenu, footer, header[data-testid="stHeader"]{ display:none; }

/* Header */
.rf-head{ display:flex; justify-content:space-between; align-items:center; background:#fff;
  border:1px solid #e2e8f0; border-radius:14px; padding:14px 18px;
  box-shadow:0 1px 3px rgba(15,23,42,.06); margin-bottom:14px; }
.rf-h1{ font-size:21px; font-weight:800; color:#0f172a; }
.rf-h1 .b{ color:#3b82f6; }
.rf-badge{ background:#e11d48; color:#fff; font-size:11px; font-weight:800; padding:2px 8px;
  border-radius:6px; margin-left:6px; letter-spacing:.3px; vertical-align:middle; }
.rf-sub{ color:#64748b; font-size:13px; margin-top:4px; }
.rf-menu{ background:#f1f5f9; border:1px solid #e2e8f0; border-radius:9px; padding:9px 14px;
  font-weight:700; font-size:13px; color:#0f172a; white-space:nowrap; }

/* Banner */
.rf-demo{ background:rgba(217,119,6,.09); border:1px solid rgba(217,119,6,.3); color:#b45309;
  border-radius:10px; padding:10px 14px; font-size:13px; font-weight:600; margin-bottom:14px; }

/* KPI cards */
.rf-kpis{ display:flex; gap:12px; margin:2px 0 14px; flex-wrap:wrap; }
.kpi{ flex:1; min-width:160px; background:#fff; border:1px solid #e2e8f0; border-radius:14px;
  padding:14px 16px; box-shadow:0 1px 2px rgba(15,23,42,.05); }
.kpi .lab{ color:#64748b; font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; }
.kpi .val{ font-size:23px; font-weight:800; margin-top:5px; color:#0f172a; }
.kpi .val.blue{ color:#3b82f6; } .kpi .val.up{ color:#16a34a; } .kpi .val.down{ color:#e11d48; }
.kpi .sub{ font-size:12.5px; margin-top:3px; font-weight:600; color:#64748b; }

/* Card + section heading */
.card{ background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:14px 16px;
  box-shadow:0 1px 3px rgba(15,23,42,.06); margin-bottom:10px; overflow-x:auto; }
.card h3{ margin:0 0 8px; font-size:14.5px; font-weight:700; color:#0f172a; }
.card .rule{ color:#64748b; font-size:12.5px; margin:-2px 0 8px; }
.sech{ font-size:17px; font-weight:800; margin:8px 0 8px; color:#0f172a; }

/* Table (bám .kpi/table gốc) */
table.rf{ width:100%; border-collapse:collapse; font-size:13px; }
table.rf th, table.rf td{ padding:9px 9px; text-align:right; border-bottom:1px solid #e2e8f0; white-space:nowrap; }
table.rf th{ color:#64748b; font-size:11px; text-transform:uppercase; letter-spacing:.4px; font-weight:600; }
table.rf th.l, table.rf td.l{ text-align:left; }
table.rf tbody tr:hover{ background:#f1f5f9; }
table.rf td.up{ color:#16a34a; font-weight:600; } table.rf td.down{ color:#e11d48; font-weight:600; }
.sector{ display:inline-block; background:#f1f5f9; border:1px solid #e2e8f0; border-radius:20px;
  padding:2px 10px; font-size:11px; color:#334155; }
.pill{ display:inline-block; background:rgba(59,130,246,.12); color:#3b82f6; font-weight:700;
  border-radius:20px; padding:2px 9px; font-size:11.5px; }

/* Tabs = .nav gốc (xám nhạt, active xanh) */
.stTabs [data-baseweb="tab-list"]{ gap:8px; border-bottom:none; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none; }
.stTabs [data-baseweb="tab"]{ background:#f1f5f9; border:1px solid #e2e8f0; border-radius:8px;
  padding:8px 16px; font-weight:700; font-size:13.5px; }
.stTabs [data-baseweb="tab"] p{ color:#0f172a !important; font-weight:700; }
.stTabs [aria-selected="true"]{ background:#3b82f6 !important; border-color:#3b82f6 !important; }
.stTabs [aria-selected="true"] p{ color:#fff !important; }

/* Buttons */
.stButton>button{ background:#3b82f6; color:#fff; border:1px solid #3b82f6; border-radius:8px;
  font-weight:700; padding:9px 18px; }
.stButton>button:hover{ filter:brightness(1.08); color:#fff; border-color:#3b82f6; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

COLLABEL = {"pe": "P/E", "pb": "P/B", "graham_no": "Graham№", "divYield": "Cổ tức", "roe": "ROE",
            "earnings_yield": "EY", "roc": "ROC", "magic_rank": "Hạng", "piotroski": "F-Score",
            "piotroskiMax": "/ Max", "netMargin": "Biên ròng", "revYoY": "DT YoY", "close": "Giá",
            "rs_rating": "RS", "ret12m": "LN 12T", "mom_12_1": "Mom 12-1", "score": "Điểm"}
DEC = {"rs_rating": 0, "score": 0, "piotroski": 0, "piotroskiMax": 0, "magic_rank": 0,
       "ret12m": 2, "mom_12_1": 2, "earnings_yield": 3, "roc": 3, "divYield": 3, "netMargin": 3,
       "revYoY": 2, "pe": 2, "pb": 2, "graham_no": 2, "close": 2, "roe": 3}


def _num(v, col):
    if pd.isna(v):
        return "—"
    d = DEC.get(col, 2)
    return f"{v:,.0f}" if d == 0 else f"{v:,.{d}f}"


def header():
    st.markdown(
        '<div class="rf-head"><div>'
        '<div class="rf-h1">RoB <span class="b">Fund</span> · Quant Engine'
        '<span class="rf-badge">BẢN HỌC THUẬT</span></div>'
        '<div class="rf-sub">Sàng lọc chiến lược huyền thoại · Tối ưu danh mục bằng thuật toán '
        'di truyền (GA) · Backtest walk-forward — dữ liệu thật TTCK Việt Nam</div>'
        '</div><div class="rf-menu">☰ Applied Big Data in Finance</div></div>',
        unsafe_allow_html=True)


def kpis(items):
    h = '<div class="rf-kpis">'
    for lab, val, sub, cls in items:
        h += f'<div class="kpi"><div class="lab">{lab}</div><div class="val {cls}">{val}</div><div class="sub">{sub}</div></div>'
    st.markdown(h + "</div>", unsafe_allow_html=True)


def sech(txt):
    st.markdown(f'<div class="sech">{txt}</div>', unsafe_allow_html=True)


def table(df, title=None, rule=None, sector_col=None, color=()):
    df = df.drop(columns=["name"]) if "name" in df.columns else df
    cols = [c for c in df.columns if c != sector_col]
    head = '<th class="l">Mã</th>' + ('<th class="l">Ngành</th>' if sector_col else "")
    head += "".join(f"<th>{COLLABEL.get(c, c)}</th>" for c in cols)
    body = ""
    for sym, r in df.iterrows():
        cells = f'<td class="l"><b>{sym}</b></td>'
        if sector_col:
            cells += f'<td class="l"><span class="sector">{r[sector_col]}</span></td>'
        for c in cols:
            v = r[c]
            cls = ("up" if v > 0 else "down") if (c in color and pd.notna(v) and v != 0) else ""
            cells += f'<td class="{cls}">{_num(v, c)}</td>'
        body += f"<tr>{cells}</tr>"
    inner = (f"<h3>{title}</h3>" if title else "") + (f'<div class="rule">{rule}</div>' if rule else "")
    inner += f'<table class="rf"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'
    st.markdown(f'<div class="card">{inner}</div>', unsafe_allow_html=True)


# =========================== Dữ liệu (cache) ===========================
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


# =========================== Trang ===========================
header()
st.markdown('<div class="rf-demo">⚠️ Sản phẩm học thuật — <b>KHÔNG phải khuyến nghị đầu tư</b>. '
            'Backtest quá khứ không đảm bảo kết quả tương lai.</div>', unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["🏆 Chiến lược", "📊 Quét thị trường", "🧬 GA Backtest", "ℹ️ Giới thiệu"])

# ---- Tab 1 ----
with t1:
    f = load_fund()
    kpis([("Rổ cổ phiếu", f"{len(f)}", "mã VN100", ""),
          ("Nguồn dữ liệu", "VNDIRECT", "BCTC & tỷ số", "blue"),
          ("Chiến lược", "3", "Graham · Magic · Piotroski", "")])
    sech("🎯 Bộ chọn chiến lược nhà đầu tư huyền thoại")
    which = st.radio("Chiến lược", ["Graham Defensive", "Magic Formula", "Piotroski F-Score"],
                     horizontal=True, label_visibility="collapsed")
    if which == "Graham Defensive":
        table(screeners.graham_defensive(f).head(12), "Graham Defensive",
              "P/E ≤ 15 · P/B ≤ 1.5 · Graham№ ≤ 22.5 · cổ tức > 0", sector_col="sector")
    elif which == "Magic Formula":
        table(screeners.magic_formula(f, top=12), "Greenblatt Magic Formula",
              "Xếp hạng Earnings Yield (1/PE) + ROC", sector_col="sector")
    else:
        mn = st.slider("Ngưỡng F-Score tối thiểu", 5, 8, 7)
        table(screeners.piotroski(f, min_score=mn), "Piotroski F-Score",
              "Chất lượng: lợi nhuận · dòng tiền · đòn bẩy · hiệu quả", sector_col="sector",
              color=("revYoY",))

# ---- Tab 2 ----
with t2:
    px, adtv = load_market()
    floors = load_floors()
    pts = int(px.notna().to_numpy().sum())
    kpis([("Số mã", f"{px.shape[1]:,}", "HOSE / HNX / UPCOM", ""),
          ("Số phiên", f"{px.shape[0]:,}", "~4 năm", ""),
          ("Điểm dữ liệu giá", f"{pts/1e6:.1f} triệu", "quy mô big data", "blue")])
    sech("🧹 Bộ lọc thanh khoản (data cleaning)")
    cc = st.columns(3)
    min_adtv = cc[0].slider("ADTV tối thiểu (tỷ VND/phiên)", 0.0, 20.0, 1.0, 0.5)
    min_price = cc[1].slider("Giá tối thiểu (nghìn VND)", 0.0, 30.0, 5.0, 1.0)
    excl = cc[2].checkbox("Loại sàn UPCOM", value=True)
    liquid = liquidity.liquid_universe(px, adtv, floors, min_adtv_bn=min_adtv,
                                       min_price=min_price, exclude_upcom=excl)
    kpis([("Trước lọc", f"{px.shape[1]}", "toàn thị trường", ""),
          ("Sau lọc", f"{len(liquid)}", "mã đầu tư được", "up")])
    pxl = px[liquid] if liquid else px
    sech("🚀 Momentum 12-1 (Jegadeesh–Titman)")
    table(sp.momentum(pxl, top=15), rule="Đà giá 12 tháng, bỏ 1 tháng gần nhất — top 15",
          color=("mom_12_1", "ret12m"))
    passed, _ = sp.minervini_trend(pxl)
    sech("📐 Minervini Trend Template")
    table(passed.head(15), rule=f"{len(passed)} mã đạt đủ 8/8 tiêu chí Stage 2 — top 15 theo RS",
          color=("ret12m",))

# ---- Tab 3 ----
with t3:
    sech("🧬 Tối ưu danh mục bằng thuật toán di truyền (GA)")
    uni = st.radio("Vũ trụ đầu tư",
                   ["Rổ VN100 chất lượng (Piotroski, demo nhanh)", "Momentum thanh khoản toàn sàn"])
    seed = st.number_input("Seed (tái lập)", 1, 9999, 42)
    if st.button("▶ Chạy toàn bộ & ra kết quả"):
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
            curves = backtest.walk_forward(px_bt, is_win=252, oos_win=63, seed=int(seed), verbose=False)
            perf = backtest.performance_table(curves)
        ga = perf.loc["GA (RoB Fund)"]
        kpis([("GA — Tổng LN", f"{ga['Tổng LN']*100:.0f}%", "out-of-sample", "up"),
              ("GA — Sharpe", f"{ga['Sharpe']:.2f}", "so với Equal-Weight", "blue"),
              ("GA — Max Drawdown", f"{ga['Max Drawdown']*100:.0f}%", "sụt giảm sâu nhất", "down")])
        pr = perf.copy()
        for c in ["Tổng LN", "CAGR", "Volatility", "Max Drawdown"]:
            pr[c] = (perf[c] * 100).round(1).astype(str) + "%"
        pr["Sharpe"] = perf["Sharpe"].round(2)
        pr.index.name = None
        rows = ""
        for name, r in pr.iterrows():
            b = "b" if "GA" in name else ""
            rows += f'<tr><td class="l"><{b or "span"}>{name}</{b or "span"}></td>' + \
                    "".join(f"<td>{r[c]}</td>" for c in pr.columns) + "</tr>"
        thead = '<th class="l">Chiến lược</th>' + "".join(f"<th>{c}</th>" for c in pr.columns)
        st.markdown(f'<div class="card"><h3>Kết quả out-of-sample</h3>'
                    f'<table class="rf"><thead><tr>{thead}</tr></thead><tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True)
        try:
            st.line_chart((1 + curves).cumprod(), color=["#3b82f6", "#94a3b8"])
        except Exception:
            st.line_chart((1 + curves).cumprod())
        st.caption(f"Vũ trụ: {px_bt.shape[1]} mã · {px_bt.shape[0]} phiên chung. "
                   "GA tối đa hoá Sharpe in-sample, trần tỷ trọng 20%, shrinkage về equal-weight.")

# ---- Tab 4 ----
with t4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("""
### Về dự án
Bản **Python** của lõi định lượng **RoB Fund** — viết lại từ sản phẩm web gốc (HTML/JS) để làm
project môn **Applied Big Data in Finance**.

**Thành phần:** screener cơ bản (Graham · Magic Formula · Piotroski) + kỹ thuật (Minervini · Momentum),
bộ lọc thanh khoản, tối ưu danh mục bằng **thuật toán di truyền (GA)**, backtest **walk-forward**.

**Dữ liệu:** VNDIRECT — cache trong `data/` để chạy offline.

**Phát hiện chính:** nếu không lọc thanh khoản, momentum "thắng ảo" nhờ micro-cap illiquid (có mã +700%);
lọc thanh khoản là bắt buộc trước khi tin backtest.

**Mã nguồn:** https://github.com/robertvo2005-ship-it/rob-fund-quant
    """)
    st.markdown('</div>', unsafe_allow_html=True)
