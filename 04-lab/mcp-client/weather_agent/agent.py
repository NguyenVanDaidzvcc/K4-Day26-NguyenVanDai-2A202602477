
"""
Weather Agent - Connects to Remote MCP Server on Cloud Run.
Uses OpenAI API through LiteLLM and Google ADK.
Successfully connects to custom MCP HTTP endpoints!
"""

from google.adk import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StreamableHTTPConnectionParams,
)

import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mặc định: server chạy local.
# Deploy lên Cloud Run thì đặt MCP_SERVER_URL trong .env
# Ví dụ: https://your-service.run.app/mcp
MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:8085/mcp"
)

# OpenAI configuration
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4.1-mini"
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY chưa được cấu hình trong .env"
    )

logger.info("Initializing weather agent with remote MCP server")
logger.info("MCP Server: %s", MCP_SERVER_URL)
logger.info("OpenAI Model: %s", OPENAI_MODEL)

try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,
    )

    # Create the MCP toolset
    logger.info("Connecting to MCP server...")

    weather_tools = McpToolset(
        connection_params=connection_params,
    )

    logger.info("MCP toolset created successfully")

    # Create the agent with OpenAI and remote MCP tools
    root_agent = Agent(
        name="weather_agent",

        model=LiteLlm(
            model=f"openai/{OPENAI_MODEL}"
        ),

        description=(
            "AI Weather Agent using OpenAI, MCP and WeatherAPI"
        ),

        instruction="""
Bạn là Weather Agent - trợ lý AI chuyên về thời tiết.

NHIỆM VỤ:
1. Trả lời người dùng hoàn toàn bằng tiếng Việt.
2. Cung cấp thông tin thời tiết từ WeatherAPI thông qua MCP.
3. Tư vấn thời tiết, kế hoạch di chuyển và hoạt động ngoài trời.

CÁCH SỬ DỤNG CÔNG CỤ:

- get_current_weather(city):
  Sử dụng khi người dùng hỏi thời tiết hiện tại.

- get_forecast(city, days):
  Sử dụng khi người dùng hỏi dự báo thời tiết.
  Hỗ trợ dự báo tối đa 3 ngày theo cấu hình hiện tại.

- health_check():
  Sử dụng khi người dùng muốn kiểm tra kết nối MCP Server.

QUY TẮC:
1. Luôn gọi công cụ phù hợp với câu hỏi thời tiết thực tế.
2. Không tự bịa nhiệt độ, độ ẩm, xác suất mưa hoặc tốc độ gió.
3. Chỉ đưa ra số liệu có trong kết quả công cụ.
4. Khi công cụ lỗi, thông báo rõ ràng cho người dùng.
5. Khi dự báo nhiều ngày, ưu tiên trình bày dưới dạng bảng.
6. Khi so sánh các thành phố, gọi công cụ cho từng thành phố.
7. Không khẳng định đã gọi tool nếu chưa nhận được kết quả.
8. Không gọi dữ liệu dự báo là số liệu quan trắc thực tế.

PHONG CÁCH TRẢ LỜI:
- Thân thiện, rõ ràng, chuyên nghiệp.
- Có thể sử dụng emoji thời tiết phù hợp.
- Đưa ra lời khuyên thực tế khi có đủ dữ liệu.
- Nêu rõ thời điểm cập nhật nếu dữ liệu có cung cấp.

Ví dụ:
Người dùng: Thời tiết Hà Nội hôm nay thế nào?
→ Gọi get_current_weather(city="Hanoi")
→ Đọc dữ liệu công cụ
→ Tổng hợp câu trả lời tiếng Việt.

Người dùng: Dự báo Hà Nội 3 ngày tới.
→ Gọi get_forecast(city="Hanoi", days=3)
→ Trình bày bảng dự báo và lời khuyên.
""",

        tools=[weather_tools],
    )

    logger.info("Weather agent initialized with OpenAI")
    logger.info("Available MCP tools:")
    logger.info("  - get_current_weather(city)")
    logger.info("  - get_forecast(city, days)")
    logger.info("  - health_check()")

except Exception:
    logger.exception(
        "Failed to initialize Weather Agent"
    )
    logger.error("MCP Server URL: %s", MCP_SERVER_URL)
    raise
