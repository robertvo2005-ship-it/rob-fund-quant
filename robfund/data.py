# -*- coding: utf-8 -*-
"""
Lớp dữ liệu — đọc BCTC (data/bctc.json) và kéo giá + khối lượng lịch sử thật từ
VNDIRECT (Python không bị CORS). Có bản kéo SONG SONG + cache đĩa cho quy mô cả sàn.
"""
from __future__ import annotations
import json, time, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

DCHART = "https://dchart-api.vndirect.com.vn/dchart/history"


def load_fundamentals(path: str = "data/bctc.json") -> pd.DataFrame:
    """Nạp BCTC thật thành DataFrame (index = mã cổ phiếu)."""
    raw = json.load(open(path, encoding="utf-8"))["data"]
    df = pd.DataFrame.from_dict(raw, orient="index")
    df.index.name = "symbol"
    return df


def _history(symbol: str, ts_from: int, ts_to: int, tries: int = 3):
    """Trả về (close, volume) theo ngày cho 1 mã, hoặc None."""
    url = f"{DCHART}?resolution=D&symbol={symbol}&from={ts_from}&to={ts_to}"
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            j = json.loads(urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore"))
            if j.get("s") != "ok" or not j.get("t"):
                return None
            idx = pd.to_datetime(j["t"], unit="s").normalize()
            close = pd.Series(j["c"], index=idx, name=symbol)
            vol = pd.Series(j.get("v", [0] * len(idx)), index=idx, name=symbol)
            return close, vol
        except Exception:
            time.sleep(0.4)
    return None


def fetch_prices(symbols: list[str], start: str = "2022-07-01", end: str | None = None,
                 cache_path: str | None = None, pause: float = 0.1, verbose: bool = True) -> pd.DataFrame:
    """Ma trận giá đóng cửa (cột = mã). Nếu có cache_path thì đọc/ghi để chạy offline."""
    if cache_path and os.path.exists(cache_path):
        px = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        if verbose:
            print(f"  (cache) {px.shape[1]} mã x {px.shape[0]} phiên ← {cache_path}")
        return px
    ts_from = int(pd.Timestamp(start).timestamp())
    ts_to = int(pd.Timestamp(end).timestamp()) if end else int(time.time())
    cols = {}
    for i, s in enumerate(symbols):
        r = _history(s, ts_from, ts_to)
        if r is not None and len(r[0]) > 60:
            cols[s] = r[0]
            if verbose:
                print(f"  [{i+1}/{len(symbols)}] {s:5} {len(r[0])} phiên")
        time.sleep(pause)
    px = pd.DataFrame(cols).sort_index()
    px = px[~px.index.duplicated(keep="last")].ffill()
    if cache_path:
        os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
        px.to_csv(cache_path)
    return px


def fetch_market(symbols: list[str], start: str = "2021-01-01", end: str | None = None,
                 max_workers: int = 16, adtv_win: int = 60,
                 cache_prices: str | None = None, cache_adtv: str | None = None,
                 verbose: bool = True):
    """
    Phiên bản "big data": kéo SONG SONG close + volume cho hàng nghìn mã, đồng thời
    tính thanh khoản ADTV (tỷ VND/phiên, trung bình `adtv_win` phiên gần nhất).
    Trả về (prices_df, adtv_series). Có cache đĩa để chạy lặp/offline.
    """
    if cache_prices and cache_adtv and os.path.exists(cache_prices) and os.path.exists(cache_adtv):
        px = pd.read_csv(cache_prices, index_col=0, parse_dates=True)
        adtv = pd.read_csv(cache_adtv, index_col=0)["adtv_bn"]
        if verbose:
            print(f"  (cache) {px.shape[1]} mã x {px.shape[0]} phiên + thanh khoản ← {cache_prices}")
        return px, adtv
    ts_from = int(pd.Timestamp(start).timestamp())
    ts_to = int(pd.Timestamp(end).timestamp()) if end else int(time.time())
    closes, adtv, done = {}, {}, 0
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for s, r in ex.map(lambda s: (s, _history(s, ts_from, ts_to)), symbols):
            done += 1
            if r is not None and len(r[0]) > 60:
                close, vol = r
                closes[s] = close
                # close (nghìn VND) * volume (cp) * 1000 = VND ; /1e9 = tỷ ; = mean(c*v)/1e6
                adtv[s] = float((close * vol).tail(adtv_win).mean()) / 1e6
            if verbose and done % 200 == 0:
                print(f"  ...{done}/{len(symbols)} mã ({time.time()-t0:.0f}s), giữ {len(closes)}")
    px = pd.DataFrame(closes).sort_index()
    px = px[~px.index.duplicated(keep="last")].ffill()
    adtv_s = pd.Series(adtv, name="adtv_bn").sort_values(ascending=False)
    if verbose:
        print(f"  Xong: {len(closes)}/{len(symbols)} mã, {px.shape[0]} phiên, {time.time()-t0:.0f}s")
    if cache_prices:
        os.makedirs(os.path.dirname(cache_prices) or ".", exist_ok=True)
        px.to_csv(cache_prices)
        adtv_s.rename("adtv_bn").to_frame().to_csv(cache_adtv)
        if verbose:
            print(f"  → cache: {cache_prices} + {cache_adtv}")
    return px, adtv_s
