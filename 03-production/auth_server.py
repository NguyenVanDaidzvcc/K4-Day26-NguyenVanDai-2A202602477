
"""MCP Server có Authentication — minh hoạ bảo mật cho production.

Server chạy qua HTTP (Streamable HTTP) thay vì stdio, kèm bearer token
verification. Chỉ request mang token hợp lệ mới được phép khám phá và gọi tool.

Luồng hoạt động:
  Client gửi request HTTP kèm header "Authorization: Bearer <token>"
    → MCP SDK xác minh token
    → Token hợp lệ → cho phép truy cập tool
    → Token sai / thiếu → trả về 401/403

Cách chạy:
    pip install -r requirements.txt
    cd 03-production
    python auth_server.py
    # Server lắng nghe tại http://127.0.0.1:8002/mcp
"""

from __future__ import annotations

import os

from pydantic import AnyHttpUrl
from mcp.server.auth.provider import AccessToken, TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer

# --- Cấu hình MCP Server ---------------------------------------------
RESOURCE_URL = "http://127.0.0.1:8002/mcp"

# --- Token store (production: dùng DB, Redis, hoặc JWT verification) ---
VALID_TOKENS: dict[str, str] = {
    os.environ.get("MCP_AUTH_TOKEN", "dev-token-abc123"): "dev-user",
    os.environ.get("MCP_SERVICE_TOKEN", "prod-key-xyz789"): "prod-service",
}


class StaticTokenVerifier(TokenVerifier):
    """Kiểm tra bearer token dựa trên danh sách tĩnh.

    Production nên thay bằng: JWT decode, OAuth introspection, hoặc
    gọi tới identity provider (Keycloak, Auth0, Google IAM, ...).
    """

    async def verify_token(self, token: str) -> AccessToken | None:
        client_id = VALID_TOKENS.get(token)

        if client_id is None:
            return None

        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=["weather:read"],
            resource=RESOURCE_URL,
        )


# --- MCP Server — logic tool không biết gì về auth --------------------
mcp = MCPServer(
    "weather-secure",
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("http://127.0.0.1:8002"),
        resource_server_url=AnyHttpUrl(RESOURCE_URL),
        required_scopes=["weather:read"],
        validate_token_resource=True,
    ),
    token_verifier=StaticTokenVerifier(),
)

_MOCK_DB = {
    "Hanoi": "29°C, trời mưa",
    "Haiphong": "33°C, mưa rào",
    "Danang": "30°C, nhiều mây",
}


@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return f"{city}: {_MOCK_DB.get(city, 'Không có dữ liệu')}"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8002,
    )
