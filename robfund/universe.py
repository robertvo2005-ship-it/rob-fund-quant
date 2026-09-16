# -*- coding: utf-8 -*-
"""
Lấy danh sách mã niêm yết toàn thị trường (HOSE/HNX/UPCOM) từ VNDIRECT.
Phục vụ mở rộng quy mô "big data" — quét cả sàn thay vì rổ VN100.
"""
from __future__ import annotations
import json, urllib.request

BASE = "https://api-finfo.vndirect.com.vn/v4"


def _fetch(size: int = 3000) -> list[dict]:
    url = f"{BASE}/stocks?q=type:STOCK~status:LISTED&size={size}&fields=code,floor,type,status"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "ignore")).get("data", [])


def listed_symbols(floors: tuple[str, ...] = ("HOSE", "HNX", "UPCOM"),
                   size: int = 3000) -> list[str]:
    return sorted({x["code"] for x in _fetch(size) if x.get("floor") in floors and x.get("code")})


def listed_with_floor(size: int = 3000) -> dict[str, str]:
    """Bản đồ mã → sàn (HOSE/HNX/UPCOM), dùng cho bộ lọc thanh khoản."""
    return {x["code"]: x["floor"] for x in _fetch(size) if x.get("code") and x.get("floor")}
