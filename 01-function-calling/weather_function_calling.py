
"""Minh hoạ FUNCTION CALLING thuần với Google Gemini SDK.

Model quyết định gọi tool; ứng dụng thực thi tool.
Dữ liệu thời tiết trong file này là giả lập.
"""

from google import genai
from google.genai import types

client = genai.Client()

MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thân thiện, trả lời bằng tiếng Việt tự nhiên. "
    "Dùng emoji phù hợp (🌧️ 🌤️ 💨 💧). "
    "Tóm tắt ngắn gọn, dễ hiểu và đưa ra lời khuyên thực tế. "
    "Đây là dữ liệu GIẢ LẬP, không phải thời tiết thực tế. "
    "Không tự đoán số liệu khi tool không có dữ liệu."
)

# 1. App tự định nghĩa schema của tool
get_weather_declaration = types.FunctionDeclaration(
    name="get_weather",
    description="Lấy thời tiết hiện tại của một thành phố",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "city": types.Schema(
                type=types.Type.STRING,
                description="Tên thành phố",
            )
        },
        required=["city"],
    ),
)

TOOLS = [types.Tool(function_declarations=[get_weather_declaration])]


# 2. App tự thực thi tool (mock)
def get_weather(city: str) -> str:
    """Trả về thời tiết giả lập của city."""
    mock_data = {
        "Hà Nội": {
            "nhiệt_độ": "29°C",
            "thời_tiết": "trời mưa nhẹ",
            "độ_ẩm": "82%",
            "gió": {"hướng": "Đông Nam", "tốc_độ": "12 km/h"},
        },
        "Hồ Chí Minh": {
            "nhiệt_độ": "33°C",
            "thời_tiết": "mưa rào",
            "độ_ẩm": "75%",
            "gió": {"hướng": "Tây Nam", "tốc_độ": "15 km/h"},
        },
        "Đà Nẵng": {
            "nhiệt_độ": "30°C",
            "thời_tiết": "nhiều mây",
            "độ_ẩm": "78%",
            "gió": {"hướng": "Đông", "tốc_độ": "10 km/h"},
        },
    }

    import json

    default = {
        "thời_tiết": "không có dữ liệu giả lập cho thành phố này"
    }

    return json.dumps(
        {"city": city, **mock_data.get(city, default)},
        ensure_ascii=False,
    )


def run(prompt: str) -> str:
    """Gửi prompt tới Gemini và xử lý function calling."""
    contents: list[types.Content] = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
    ]

    # 3. Model quyết định có gọi tool hay không
    resp = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            tools=TOOLS,
            system_instruction=SYSTEM_INSTRUCTION,
        ),
    )

    # 4. App tự thực thi các tool model yêu cầu
    tool_rounds = 0

    while resp.function_calls:
        tool_rounds += 1

        if tool_rounds > 5:
            raise RuntimeError(
                "Model gọi tool quá 5 vòng — dừng để tránh lặp vô hạn"
            )

        contents.append(resp.candidates[0].content)

        function_responses = []

        for fc in resp.function_calls:
            print(f"  [model yêu cầu] {fc.name}({fc.args})")

            if (
                fc.name == "get_weather"
                and isinstance((fc.args or {}).get("city"), str)
            ):
                result = get_weather(city=fc.args["city"])
            else:
                result = "Lỗi: tool hoặc tham số không hợp lệ"

            print(f"  [app thực thi] -> {result}")

            function_responses.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": result},
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=function_responses,
            )
        )

        resp = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )

    # 5. Model tổng hợp câu trả lời
    return resp.text or "Model không tạo câu trả lời."


if __name__ == "__main__":
    question = "Thời tiết Hà Nội và Đà Nẵng hôm nay thế nào?"
    print(f"User: {question}\n")
    print("Trả lời:", run(question))
