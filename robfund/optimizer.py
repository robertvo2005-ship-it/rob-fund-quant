# -*- coding: utf-8 -*-
"""
Tối ưu phân bổ vốn bằng THUẬT TOÁN DI TRUYỀN (GA) — lõi "AI-assisted" của RoB Fund.
Port ý tưởng từ bản JS: tối đa hoá Sharpe in-sample, có trần tỷ trọng + co ngót
(shrinkage) về danh mục đều để giảm overfit. Cố định seed để tái lập được.
"""
from __future__ import annotations
import numpy as np

TRADING_DAYS = 252


def _normalize(w: np.ndarray, cap: float) -> np.ndarray:
    """Không âm, tổng = 1, áp trần tỷ trọng rồi chuẩn hoá lại."""
    w = np.clip(w, 0, None)
    s = w.sum()
    w = np.full_like(w, 1.0 / len(w)) if s <= 0 else w / s
    for _ in range(10):  # ép trần lặp cho hội tụ
        over = w > cap
        if not over.any():
            break
        excess = (w[over] - cap).sum()
        w[over] = cap
        under = ~over
        if under.any():
            w[under] += excess * w[under] / w[under].sum()
        w = np.clip(w, 0, None); w /= w.sum()
    return w


def _sharpe(weights: np.ndarray, rets: np.ndarray) -> float:
    port = rets @ weights
    sd = port.std()
    return 0.0 if sd == 0 else (port.mean() / sd) * np.sqrt(TRADING_DAYS)


def optimize_ga(rets: np.ndarray, *, pop: int = 60, gens: int = 40, cap: float = 0.20,
                shrink: float = 0.25, elite: int = 4, seed: int = 42) -> np.ndarray:
    """
    Trả về vector tỷ trọng tối ưu.
      rets   : ma trận lợi suất in-sample (T x N)
      cap    : trần tỷ trọng mỗi mã
      shrink : hệ số co ngót về equal-weight (0..1) — kỷ luật hoá, chống overfit
    """
    rng = np.random.default_rng(seed)
    n = rets.shape[1]
    eq = np.full(n, 1.0 / n)

    def finalize(w):
        w = (1 - shrink) * w + shrink * eq   # co ngót về danh mục đều
        return _normalize(w, cap)

    P = np.array([finalize(rng.random(n)) for _ in range(pop)])
    for _ in range(gens):
        fit = np.array([_sharpe(w, rets) for w in P])
        order = np.argsort(fit)[::-1]
        P, fit = P[order], fit[order]
        nxt = [P[i].copy() for i in range(elite)]              # elitism
        while len(nxt) < pop:
            a, b = (P[min(rng.integers(0, pop), rng.integers(0, pop))] for _ in range(2))  # tournament
            alpha = rng.random()
            child = alpha * a + (1 - alpha) * b                # lai ghép số học
            if rng.random() < 0.30:                            # đột biến
                child = child + rng.normal(0, 0.05, n)
            nxt.append(finalize(child))
        P = np.array(nxt)
    fit = np.array([_sharpe(w, rets) for w in P])
    return P[int(np.argmax(fit))]
