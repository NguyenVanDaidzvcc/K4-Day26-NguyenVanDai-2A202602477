
"""Day 26 / 02: MCP Server qua stdio, không cần API key.

Chú ý: Các giá trị đều là mock để minh họa MCP, không phải dự báo thật.
"""

from __future__ import annotations

import json
import unicodedata

from mcp.server import MCPServer

mcp = MCPServer("weather-demo")

DATA = {
    "hanoi": {
        "city": "Hanoi",
        "temp_c": 29,
        "condition": "mưa nhẹ",
    },
    "danang": {
        "city": "Danang",
        "temp_c": 30,
        "condition": "nhiều mây",
    },
    "haiphong": {
        "city": "Haiphong",
        "temp_c": 33,
        "condition": "mưa rào",
    },
}

ALIASES = {
    "ha noi": "hanoi",
    "da nang": "danang",
    "hai phong": "haiphong",
}


def lookup(city: str) -> dict | None:
    normalized = unicodedata.normalize(
        "NFD", city.lower().replace("đ", "d")
    )
    key = " ".join(
        "".join(ch for ch in normalized if not unicodedata.combining(ch)).split()
    )
    return DATA.get(ALIASES.get(key, key))


@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết HIỆN TẠI giả lập của một thành phố."""
    data = lookup(city)
    if data is None:
        return json.dumps(
            {"city": city, "error": "Không có dữ liệu mock"},
            ensure_ascii=False,
        )
    return json.dumps(
        {**data, "source": "mock"},
        ensure_ascii=False,
    )


@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Lấy DỰ BÁO GIẢ LẬP 1-3 ngày để thực hành khám phá MCP tool."""
    if not 1 <= days <= 3:
        return json.dumps(
            {"error": "days phải từ 1 đến 3"},
            ensure_ascii=False,
        )

    data = lookup(city)
    if data is None:
        return json.dumps(
            {"city": city, "error": "Không có dữ liệu mock"},
            ensure_ascii=False,
        )

    variations = [-1, 1, 0]
    conditions = ["nhiều mây", "nắng nhẹ", "mưa rào"]

    forecast = [
        {
            "day_offset": offset + 1,
            "temp_c": data["temp_c"] + variations[offset],
            "condition": conditions[offset],
        }
        for offset in range(days)
    ]

    return json.dumps(
        {
            "city": data["city"],
            "source": "mock",
            "forecast": forecast,
        },
        ensure_ascii=False,
    )


if __name__ == "__main__":
    mcp.run()  # stdio: client tạo tiến trình server
