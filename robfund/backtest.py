# -*- coding: utf-8 -*-
"""
Backtest walk-forward + đo hiệu quả. Cửa sổ in-sample tối ưu GA, áp tỷ trọng ra
cửa sổ out-of-sample kế tiếp rồi lăn tới (rebalance định kỳ) — đúng cơ chế bản gốc.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .optimizer import optimize_ga, TRADING_DAYS


def _metrics(daily: pd.Series) -> dict:
    eq = (1 + daily).cumprod()
    years = len(daily) / TRADING_DAYS
    cagr = eq.iloc[-1] ** (1 / years) - 1 if years > 0 else np.nan
    vol = daily.std() * np.sqrt(TRADING_DAYS)
    sharpe = (daily.mean() / daily.std() * np.sqrt(TRADING_DAYS)) if daily.std() else np.nan
    mdd = (eq / eq.cummax() - 1).min()
    return {"Tổng LN": eq.iloc[-1] - 1, "CAGR": cagr, "Volatility": vol,
            "Sharpe": sharpe, "Max Drawdown": mdd}


def walk_forward(prices: pd.DataFrame, *, is_win: int = 252, oos_win: int = 63,
                 seed: int = 42, verbose: bool = True) -> pd.DataFrame:
    """
    So sánh GA (tối ưu Sharpe, có shrinkage) vs Equal-Weight trên cùng dữ liệu OOS.
    Trả về DataFrame equity curve của 2 chiến lược.
    """
    rets = prices.pct_change().dropna()
    R = rets.values
    dates = rets.index
    n = R.shape[1]
    ga_oos, eq_oos, oos_dates = [], [], []
    start = is_win
    step = 0
    while start + oos_win <= len(R):
        is_slice = R[start - is_win:start]
        oos_slice = R[start:start + oos_win]
        w_ga = optimize_ga(is_slice, seed=seed + step)
        w_eq = np.full(n, 1.0 / n)
        ga_oos.append(oos_slice @ w_ga)
        eq_oos.append(oos_slice @ w_eq)
        oos_dates.append(dates[start:start + oos_win])
        if verbose:
            top = np.argsort(w_ga)[::-1][:3]
            picks = ", ".join(f"{prices.columns[i]} {w_ga[i]*100:.0f}%" for i in top)
            print(f"  rebalance {step+1}: top GA → {picks}")
        start += oos_win
        step += 1
    idx = np.concatenate([d.values for d in oos_dates])
    out = pd.DataFrame({
        "GA (RoB Fund)": np.concatenate(ga_oos),
        "Equal-Weight": np.concatenate(eq_oos),
    }, index=pd.DatetimeIndex(idx))
    return out


def performance_table(daily_rets: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({c: _metrics(daily_rets[c]) for c in daily_rets.columns}).T
