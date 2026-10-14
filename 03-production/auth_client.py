
"""MCP Client có Authentication — kết nối tới auth_server.py qua HTTP.

Client tạo HTTP client bằng httpx2.AsyncClient(headers=...).
Header Authorization được gắn vào mọi request HTTP tới server.

Cách chạy (cần auth_server.py đang chạy ở terminal khác):
    cd 03-production
    python auth_server.py            # terminal 1
    python auth_client.py            # terminal 2
"""

from __future__ import annotations

import asyncio
import os

import httpx2

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SERVER_URL = "http://127.0.0.1:8002/mcp"
TOKEN = os.environ.get("MCP_AUTH_TOKEN", "dev-token-abc123")


async def main() -> None:
    http_client = httpx2.AsyncClient(
        headers={"Authorization": f"Bearer {TOKEN}"},
        timeout=httpx2.Timeout(30.0, read=300.0),
    )

    async with http_client:
        async with streamable_http_client(
            SERVER_URL,
            http_client=http_client,
        ) as (read, write):

            async with ClientSession(read, write) as session:
                await session.initialize()

                # 1. Liệt kê danh sách tool
                tools = await session.list_tools()

                print("Tools (có auth):")
                for t in tools.tools:
                    print(f"  - {t.name}: {t.description}")

                # 2. Gọi tool lấy thời tiết
                result = await session.call_tool(
                    "get_weather",
                    {"city": "Hanoi"},
                )

                if result.is_error:
                    raise RuntimeError(
                        f"Tool lỗi: {result.content}"
                    )

                print(f"\nKết quả: {result.content[0].text}")
                print("\nPASS: Authentication thành công!")


if __name__ == "__main__":
    asyncio.run(main())
