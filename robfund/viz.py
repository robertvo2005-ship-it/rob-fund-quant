# -*- coding: utf-8 -*-
"""Vẽ đường vốn (tuỳ chọn — cần matplotlib). Không có matplotlib thì bỏ qua, không lỗi."""
from __future__ import annotations
import pandas as pd


def plot_equity(curves: pd.DataFrame, title: str, path: str) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("  (bỏ qua biểu đồ — chưa cài matplotlib)")
        return False
    eq = (1 + curves).cumprod()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    colors = {"GA (RoB Fund)": "#2563eb", "Equal-Weight": "#f59e0b"}
    for col in eq.columns:
        tot = (eq[col].iloc[-1] - 1) * 100
        ax.plot(eq.index, eq[col], lw=2 if "GA" in col else 1.6,
                ls="-" if "GA" in col else "--",
                color=colors.get(col, "#9ca3af"), label=f"{col}  {tot:+.0f}%")
    ax.set_title(title); ax.set_ylabel("Giá trị 1 đồng vốn")
    ax.legend(loc="upper left"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(path, dpi=130)
    print(f"  → biểu đồ: {path}")
    return True
