
"""MCP CLIENT — kết nối weather_server.py qua stdio.

Client khám phá tool tại runtime và gọi tool qua MCP.
Không cần Gemini API key.

Chạy: python weather_client.py
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Dùng đúng Python interpreter đang chạy client
    server_path = Path(__file__).with_name("weather_server.py").resolve()

    params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Khám phá tools
            tools = await session.list_tools()
            print("Tools server cung cấp:")

            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            # 2. Gọi tool lấy thời tiết hiện tại
            for city in ["Hanoi", "Danang", "Haiphong"]:
                result = await session.call_tool(
                    "get_weather",
                    {"city": city},
                )

                print(f"\ncall_tool get_weather(city={city!r}):")

                if result.is_error:
                    raise RuntimeError(
                        f"get_weather thất bại: {result.content}"
                    )

                print("  ->", result.content[0].text)

            # 3. Gọi tool dự báo (nếu server hỗ trợ)
            if "get_forecast" in {t.name for t in tools.tools}:
                result = await session.call_tool(
                    "get_forecast",
                    {"city": "Hanoi", "days": 3},
                )

                if result.is_error:
                    raise RuntimeError(
                        f"get_forecast thất bại: {result.content}"
                    )

                print(
                    "\nDự báo 3 ngày [MOCK]:",
                    result.content[0].text,
                )


if __name__ == "__main__":
    asyncio.run(main())
