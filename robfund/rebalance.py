# -*- coding: utf-8 -*-
"""
Tái cân bằng danh mục về mục tiêu (từ Quyết định) — port cơ chế đảo lệnh của bản gốc:
so vị thế đang nắm với tỷ trọng mục tiêu (scale theo NAV hiện tại) → lệnh MUA/BÁN.
Khi áp: bán hiện thực hoá lãi/lỗ (cộng thẳng vào tiền mặt), ghi từng lệnh vào nhật ký.
"""
from __future__ import annotations
import pandas as pd


def _price(prices: pd.DataFrame, s: str):
    return round(float(prices[s].dropna().iloc[-1]) * 1000) if s in prices.columns else None


def compute_orders(positions: list[dict], cash: float, decision: dict, prices: pd.DataFrame):
    cur = {p["sym"]: p for p in positions}
    curval = sum(p["shares"] * (_price(prices, p["sym"]) or 0) for p in positions)
    nav = curval + cash
    tgt = {}
    for r in decision["rec"]:
        if r["weight"] > 0:
            price = _price(prices, r["sym"]) or r["price"]
            tgt[r["sym"]] = max(0, int((r["weight"] * nav) // price // 100) * 100)
    orders = []
    for s in dict.fromkeys(list(cur) + list(tgt)):
        price = _price(prices, s) or (cur[s]["cost"] if s in cur else 0)
        cs = cur[s]["shares"] if s in cur else 0
        ts = tgt.get(s, 0)
        d = ts - cs
        act = ("MUA MỚI" if cs == 0 and ts > 0 else "BÁN HẾT" if ts == 0 and cs > 0
               else "MUA THÊM" if d > 0 else "BÁN BỚT" if d < 0 else "GIỮ NGUYÊN")
        orders.append(dict(sym=s, action=act, cur=cs, tgt=ts, delta=d, price=price,
                           cost=cur[s]["cost"] if s in cur else price))
    return orders, nav


def apply_orders(positions: list[dict], cash: float, orders: list[dict]):
    cur = {p["sym"]: dict(p) for p in positions}
    realized, new_cash = 0, float(cash)
    jentries = []
    today = str(pd.Timestamp.today().normalize().date())
    for o in orders:
        s, d, price = o["sym"], o["delta"], o["price"]
        if d == 0:
            continue
        if d > 0:  # MUA
            new_cash -= d * price
            if s in cur:
                p = cur[s]; tot = p["shares"] + d
                p["cost"] = round((p["shares"] * p["cost"] + d * price) / tot)
                p["shares"] = tot
            else:
                cur[s] = dict(sym=s, shares=d, cost=price)
            jentries.append(dict(date=today, sym=s, action="MUA", shares=d, price=price,
                                 note="Tái cân bằng"))
        else:      # BÁN — hiện thực hoá lãi/lỗ
            q = -d
            new_cash += q * price
            pnl = q * (price - cur[s]["cost"]) if s in cur else 0
            realized += pnl
            if s in cur:
                cur[s]["shares"] -= q
                if cur[s]["shares"] <= 0:
                    del cur[s]
            _pnl = f"{pnl:+,.0f}".replace(",", ".")
            jentries.append(dict(date=today, sym=s, action="BÁN", shares=q, price=price,
                                 note=f"Tái cân bằng · LĐ đã thực hiện {_pnl}đ"))
    return list(cur.values()), int(round(new_cash)), int(round(realized)), jentries
