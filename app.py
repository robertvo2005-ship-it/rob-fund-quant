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
from robfund import data, screeners, screeners_price as sp, liquidity, backtest, decision, portfolio as pf

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


STANCE_SHORT = {"down": "PHÒNG THỦ — thị trường giảm", "side": "THẬN TRỌNG — đi ngang",
                "up_vol": "TĂNG nhưng rung lắc — chọn lọc", "up": "THUẬN LỢI — tăng ổn định"}


def fmtint(v):
    return f"{int(round(v)):,}".replace(",", ".")


def fmtvnd(v):
    return fmtint(v) + "đ"


def zbadge(z):
    def b(lab, v):
        c = "#16a34a" if v >= 0.5 else ("#e11d48" if v <= -0.5 else "#64748b")
        return f'<span style="color:{c};font-size:10.5px;margin-right:8px;white-space:nowrap">{lab} {v:+.1f}</span>'
    return b("Xu hướng", z["trend200"]) + b("Ít b.động", z["lowvol"]) + b("Đà", z["mom"])


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


@st.cache_data
def load_vnindex():
    return pd.read_csv("data/vnindex.csv", index_col=0, parse_dates=True)["close"]


@st.cache_data
def load_portfolio():
    return pf.load_portfolio("data/portfolio.json")


@st.cache_data
def load_journal():
    return pf.load_journal("data/journal.csv")


# =========================== Trang ===========================
header()
st.markdown('<div class="rf-demo">⚠️ Sản phẩm học thuật — <b>KHÔNG phải khuyến nghị đầu tư</b>. '
            'Backtest quá khứ không đảm bảo kết quả tương lai.</div>', unsafe_allow_html=True)

# Trạng thái danh mục dùng chung giữa tab Quyết định & Danh mục
if "pf" not in st.session_state:
    _p = load_portfolio()
    st.session_state.pf = dict(cash=int(_p["cash"]), inception=_p["inception"],
                               positions=[dict(p) for p in _p["positions"]],
                               journal=load_journal().to_dict("records"))
    st.session_state.pf_ver = 0

t0, tdm, t1, t2, t3, t4 = st.tabs(
    ["🧭 Quyết định", "💼 Danh mục", "🏆 Chiến lược", "📊 Quét thị trường",
     "🧬 GA Backtest", "ℹ️ Giới thiệu"])

# ---- Tab 0: Quyết định đầu tư (chạy GA ra danh mục cụ thể) ----
with t0:
    f = load_fund()
    px, adtv = load_market()
    vni = load_vnindex()
    universe = [s for s in f.index if s in px.columns]
    sech("🎯 Quyết định đầu tư — chạy GA ra danh mục cụ thể")
    cc = st.columns([1.4, 1, 1])
    nav = cc[0].number_input("Vốn đầu tư (VND)", 10_000_000, 100_000_000_000,
                             500_000_000, 10_000_000)
    hz = cc[1].selectbox("Khung thời gian", ["short", "mid", "long"], index=1,
                         format_func=lambda x: {"short": "Ngắn (3 mã)", "mid": "Trung (5 mã)",
                                                "long": "Dài (8 mã)"}[x])
    cash0 = cc[2].slider("Tiền mặt mục tiêu", 0.0, 0.6, 0.30, 0.05)
    if st.button("▶ Chạy toàn bộ & ra quyết định", key="decbtn"):
        with st.spinner("① Dữ liệu → ② Regime → ③ Factor long-only → ④ GA phân bổ vốn..."):
            st.session_state.decision = decision.build_decision(
                px, universe, vni, nav=nav, base_cash=cash0, horizon=hz)

    D = st.session_state.get("decision")
    if D:
        reg = D["reg"]
        st.markdown(
            f'<div class="card" style="border-left:5px solid {reg["color"]}">'
            f'<b style="color:{reg["color"]}">② Regime: {reg["label"]}</b> — {reg["detail"]}<br>'
            f'<span style="color:#64748b">🧭 {reg["stance"]}</span></div>', unsafe_allow_html=True)
        act = f"MUA {D['n_buy']} mã" if D["n_buy"] else "ĐỨNG NGOÀI"
        k = ('<div class="rf-kpis">'
             f'<div class="kpi"><div class="lab">Trạng thái thị trường</div>'
             f'<div class="val" style="font-size:17px;color:{reg["color"]}">{reg["label"]}</div>'
             f'<div class="sub">{STANCE_SHORT.get(reg["state"], "")}</div></div>'
             f'<div class="kpi"><div class="lab">Khuyến nghị hành động</div>'
             f'<div class="val" style="font-size:17px">{act}</div>'
             f'<div class="sub">độ tin cậy: {D["convict"]}</div></div>'
             f'<div class="kpi"><div class="lab">Triển khai / Tiền mặt</div>'
             f'<div class="val">{(1-D["cash_t"])*100:.0f}% / {D["cash_t"]*100:.0f}%</div>'
             f'<div class="sub">đã phân bổ {fmtvnd(D["invested"])}</div></div>'
             f'<div class="kpi"><div class="lab">Số vị thế</div>'
             f'<div class="val">{D["n_buy"]} / {D["max_pos"]}</div>'
             f'<div class="sub">theo trần IPS</div></div></div>')
        st.markdown(k, unsafe_allow_html=True)
        sec = f["sector"].to_dict()
        rows = ""
        for r in D["rec"]:
            rows += ("<tr>"
                     f'<td class="l"><b>{r["sym"]}</b>'
                     f'<div style="color:#64748b;font-size:11px">{sec.get(r["sym"], "")}</div></td>'
                     f'<td><b>{r["weight"]*100:.1f}%</b></td>'
                     f'<td>{fmtint(r["shares"])}</td>'
                     f'<td>{fmtvnd(r["actual"])}</td>'
                     f'<td>{fmtvnd(r["price"])}</td>'
                     f'<td class="down">{fmtvnd(r["stop"])}</td>'
                     f'<td class="up">{fmtvnd(r["target"])}</td>'
                     f'<td class="l">{zbadge(r["z"])}</td></tr>')
        rows += ('<tr style="border-top:2px solid #e2e8f0"><td class="l"><b>Tiền mặt</b></td>'
                 f'<td><b>{D["cash_t"]*100:.0f}%</b></td>'
                 f'<td colspan="6">{fmtvnd(D["nav"]-D["invested"])}</td></tr>')
        head = ('<th class="l">Mã</th><th>Tỷ trọng</th><th>KL</th><th>Số tiền</th>'
                '<th>Giá vào</th><th>Stop</th><th>Target</th>'
                '<th class="l">Điểm factor (z trong rổ)</th>')
        st.markdown(f'<div class="card"><h3>🎯 Danh sách MUA</h3>'
                    f'<table class="rf"><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True)
        st.markdown(
            '<div class="rf-demo" style="background:#eff6ff;border-color:#bfdbfe;color:#1e40af">'
            f'<b>Mạch quyết định:</b> ① Dữ liệu → ② Regime (<b>{reg["label"]}</b>) → '
            f'③ Factor long-only (horizon {hz}, {D["n_pos"]} mã, tái cân bằng {D["reb"]}) → '
            f'④ Phân bổ <b>{D["scheme"]}</b> theo regime (tiền mặt {D["cash_t"]*100:.0f}%) → '
            '🎯 Danh sách MUA. Stop −8%, target R/R 1:3. Đây là <b>hỗ trợ quyết định</b>, '
            'KHÔNG phải khuyến nghị đầu tư.</div>', unsafe_allow_html=True)
        if st.button("✅ Áp vào danh mục", key="applybtn"):
            _buys = [r for r in D["rec"] if r["shares"] > 0]
            _today = str(pd.Timestamp.today().normalize().date())
            st.session_state.pf["positions"] = [
                dict(sym=r["sym"], shares=r["shares"], cost=r["price"]) for r in _buys]
            st.session_state.pf["cash"] = int(round(D["nav"] - D["invested"]))
            st.session_state.pf["inception"] = _today
            st.session_state.pf["just_applied"] = True
            for r in _buys:
                st.session_state.pf["journal"].append(dict(
                    date=_today, sym=r["sym"], action="MUA", shares=r["shares"],
                    price=r["price"], note="Áp từ Quyết định (giá vốn = giá vào)"))
            st.session_state.pf_ver += 1
            st.success(f"✅ Đã áp {len(_buys)} mã vào danh mục (giá vốn = giá vào) · "
                       f"tiền mặt còn {fmtvnd(st.session_state.pf['cash'])}. "
                       "Mở tab 💼 Danh mục để xem NAV & nhật ký.")
    else:
        st.markdown('<div class="card" style="color:#64748b">Nhập vốn & bấm '
                    '<b>▶ Chạy toàn bộ & ra quyết định</b> — engine sẽ: nhận diện <b>regime</b> '
                    'thị trường → xếp hạng <b>factor</b> long-only → <b>GA</b> phân bổ vốn → ra '
                    '<b>danh mục MUA cụ thể</b> (tỷ trọng, KL, giá vào, stop, target, điểm factor).</div>',
                    unsafe_allow_html=True)

# ---- Tab: Danh mục đang nắm + Nhật ký + đường NAV ----
with tdm:
    px, _ = load_market()
    vni = load_vnindex()
    fund = load_fund()
    vn100 = [s for s in fund.index if s in px.columns]
    P = st.session_state.pf
    ver = st.session_state.pf_ver

    sech("💼 Danh mục đang nắm")
    if P.get("just_applied"):
        st.success("✅ Danh mục vừa được áp từ tab Quyết định (giá vốn = giá vào ngày áp).")
        P["just_applied"] = False
    cc = st.columns([1.2, 1])
    cash = cc[0].number_input("Tiền mặt (VND)", 0, 100_000_000_000, int(P["cash"]),
                              10_000_000, key=f"cash_{ver}")
    incep = cc[1].text_input("Ngày lập danh mục", P["inception"], key=f"incep_{ver}")
    edited = st.data_editor(
        pd.DataFrame(P["positions"]), num_rows="dynamic", use_container_width=True,
        key=f"hold_{ver}",
        column_config={"sym": st.column_config.TextColumn("Mã"),
                       "shares": st.column_config.NumberColumn("Khối lượng", step=100),
                       "cost": st.column_config.NumberColumn("Giá vốn (VND)", step=100)})
    positions = [dict(sym=str(r["sym"]).upper().strip(), shares=int(r["shares"]), cost=int(r["cost"]))
                 for _, r in edited.iterrows()
                 if pd.notna(r.get("sym")) and pd.notna(r.get("shares")) and pd.notna(r.get("cost"))
                 and str(r["sym"]).upper().strip() in px.columns]

    if positions:
        h = pf.holdings_table(positions, px)
        mv = float(h["value"].sum()); pnl = float(h["pnl"].sum()); nav_now = mv + cash
        _idx = px.index[px.index >= pd.Timestamp(incep)]
        has_hist = len(_idx) >= 5
        reb, nav_r, vni_r, v100_r = None, 0.0, 0.0, 0.0
        if has_hist:
            nav = pf.nav_series(positions, cash, incep, px)
            vni_c, ew = pf.benchmark_curves(incep, px, vni, vn100)
            reb = pf.rebased_100(nav, vni_c, ew)
            nav_r = float(reb["Danh mục (NAV)"].iloc[-1] - 100)
            vni_r = float(reb["VN-Index"].iloc[-1] - 100)
            v100_r = float(reb["VN100 (EW)"].iloc[-1] - 100)
        if has_hist:
            navcard = (f'<div class="val {"up" if nav_r>=0 else "down"}">{nav_r:+.1f}%</div>'
                       f'<div class="sub">VN-Index {vni_r:+.1f}% · VN100 {v100_r:+.1f}%</div>')
            alphacard = (f'<div class="val {"up" if nav_r>=vni_r else "down"}">{nav_r-vni_r:+.1f}</div>'
                         f'<div class="sub">điểm % so với chỉ số</div>')
        else:
            navcard = '<div class="val">vừa lập</div><div class="sub">NAV hình thành theo thời gian</div>'
            alphacard = '<div class="val">—</div><div class="sub">chưa đủ lịch sử</div>'
        st.markdown(
            '<div class="rf-kpis">'
            f'<div class="kpi"><div class="lab">NAV hiện tại</div><div class="val">{fmtvnd(nav_now)}</div>'
            f'<div class="sub">gồm tiền mặt {fmtvnd(cash)}</div></div>'
            f'<div class="kpi"><div class="lab">Lãi/lỗ cổ phiếu</div>'
            f'<div class="val {"up" if pnl>=0 else "down"}">{"+" if pnl>=0 else ""}{fmtvnd(pnl)}</div>'
            f'<div class="sub">chưa hiện thực</div></div>'
            f'<div class="kpi"><div class="lab">NAV từ ngày lập</div>{navcard}</div>'
            f'<div class="kpi"><div class="lab">Alpha vs VN-Index</div>{alphacard}</div></div>',
            unsafe_allow_html=True)

        head = ('<th class="l">Mã</th><th>KL</th><th>Giá vốn</th><th>Giá hiện tại</th>'
                '<th>Giá trị</th><th>Lãi/lỗ</th><th>%</th>')
        rows = ""
        for sym, r in h.iterrows():
            cls = "up" if r["pnl"] >= 0 else "down"; sg = "+" if r["pnl"] >= 0 else ""
            rows += (f'<tr><td class="l"><b>{sym}</b></td><td>{fmtint(r["shares"])}</td>'
                     f'<td>{fmtvnd(r["cost"])}</td><td>{fmtvnd(r["price"])}</td><td>{fmtvnd(r["value"])}</td>'
                     f'<td class="{cls}">{sg}{fmtvnd(r["pnl"])}</td>'
                     f'<td class="{cls}">{r["pct"]*100:+.1f}%</td></tr>')
        clsT = "up" if pnl >= 0 else "down"
        rows += (f'<tr style="border-top:2px solid #e2e8f0"><td class="l"><b>Tổng CP</b></td>'
                 f'<td colspan="3"></td><td><b>{fmtvnd(mv)}</b></td>'
                 f'<td class="{clsT}"><b>{("+" if pnl>=0 else "")}{fmtvnd(pnl)}</b></td><td></td></tr>')
        st.markdown(f'<div class="card"><table class="rf"><thead><tr>{head}</tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>', unsafe_allow_html=True)

        sech("📈 Đường NAV so với VN-Index & VN100")
        if has_hist and reb is not None:
            try:
                st.line_chart(reb, color=["#3b82f6", "#e11d48", "#d97706"])
            except Exception:
                st.line_chart(reb)
            st.caption("Các đường quy về 100 tại ngày lập danh mục · VN100 (EW) = chỉ số trung bình "
                       "đều giá VN100 · danh mục giả định buy-and-hold từ ngày lập.")
        else:
            st.info("Danh mục vừa được lập gần đây — đường NAV sẽ hình thành theo thời gian. "
                    "Đổi 'Ngày lập danh mục' về sớm hơn (VD 2024-01-02) để xem so sánh dài hạn.")
    else:
        st.info("Chưa có vị thế hợp lệ — nhập Mã (có trong dữ liệu) / Khối lượng / Giá vốn ở bảng trên.")

    sech("📒 Nhật ký giao dịch")
    jhead = ('<th class="l">Ngày</th><th class="l">Mã</th><th class="l">Lệnh</th>'
             '<th>KL</th><th>Giá</th><th class="l">Ghi chú</th>')
    jrows = ""
    for r in reversed(P["journal"]):
        act = str(r["action"]); cls = "up" if act == "MUA" else "down"
        jrows += (f'<tr><td class="l">{r["date"]}</td><td class="l"><b>{r["sym"]}</b></td>'
                  f'<td class="l {cls}"><b>{act}</b></td><td>{fmtint(r["shares"])}</td>'
                  f'<td>{fmtvnd(r["price"])}</td>'
                  f'<td class="l" style="color:#64748b">{r["note"]}</td></tr>')
    st.markdown(f'<div class="card"><table class="rf"><thead><tr>{jhead}</tr></thead>'
                f'<tbody>{jrows}</tbody></table></div>', unsafe_allow_html=True)
    st.caption("Dữ liệu danh mục & nhật ký là MẪU (chỉnh sửa bảng phía trên để cập nhật NAV theo thời gian thực).")


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
