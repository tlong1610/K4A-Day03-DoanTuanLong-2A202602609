"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import time
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"), override=True)

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        import re
        prompt_lower = prompt.lower()
        match = re.search(r"vd\d+", prompt_lower)
        tracking_code = match.group(0).upper() if match else "VD2609001"

        # Đã có Observation từ vòng trước: quyết định gọi tool tiếp hoặc trả lời cuối
        if "[observation" in prompt_lower:
            already_updated = "update_id" in prompt_lower
            still_waiting = "chờ xuất kho" in prompt_lower and any(
                keyword in prompt_lower for keyword in ["cập nhật", "xuất kho"]
            )
            if still_waiting and not already_updated:
                return {
                    "type": "tool_call",
                    "tool_name": "update_order_status",
                    "arguments": {
                        "tracking_code": tracking_code,
                        "new_status": "Đã xuất kho",
                        "warehouse_location": "Kho Linh kiện Hải Phòng"
                    },
                    "thought": f"Đã xác nhận đơn {tracking_code} đang chờ xuất kho. Tôi sẽ gọi update_order_status."
                }
            return {
                "type": "text",
                "content": "",
                "thought": "Đã nhận Observation, đưa ra câu trả lời cuối cùng."
            }

        # Mô phỏng nhận diện intent gọi Tool kho vận
        if any(keyword in prompt_lower for keyword in ["cập nhật", "xuất kho", "đã giao"]) and "nếu" not in prompt_lower:
            new_status = "Đã giao hàng" if "giao" in prompt_lower else "Đã xuất kho"
            warehouse = "Kho Trung tâm Bắc Ninh" if "bắc ninh" in prompt_lower else "Kho Linh kiện Hải Phòng"
            return {
                "type": "tool_call",
                "tool_name": "update_order_status",
                "arguments": {
                    "tracking_code": tracking_code,
                    "new_status": new_status,
                    "warehouse_location": warehouse
                },
                "thought": f"Người dùng yêu cầu cập nhật trạng thái đơn {tracking_code}. Tôi sẽ gọi tool update_order_status."
            }
        elif tracking_code.startswith("VD") and (
            "tra cứu" in prompt_lower or "vị trí" in prompt_lower or "mã vận đơn" in prompt_lower or match
        ):
            return {
                "type": "tool_call",
                "tool_name": "track_shipment",
                "arguments": {"tracking_code": tracking_code},
                "thought": f"Người dùng muốn tra cứu mã vận đơn {tracking_code}. Tôi sẽ gọi tool track_shipment."
            }
        else:
            return {
                "type": "text",
                "content": (
                    "[Mock Agent Response]: Xin chào! Quy trình kho vận chuẩn gồm 5 bước: "
                    "nhận hàng vào kho, lưu vị trí (kho/dãy/ô), soạn xuất, bàn giao vận chuyển và xác nhận đã giao. "
                    "Mỗi đơn phải có mã vận đơn để truy vết trạng thái."
                ),
                "thought": "Câu hỏi chung về quy trình kho vận, trả lời trực tiếp không cần gọi Tool."
            }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-3.6-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait_match = re.search(r"retry in ([\d.]+)s", err, re.IGNORECASE)
                wait_s = int(float(wait_match.group(1))) + 2 if wait_match else 45
                print(f"⏳ [Gemini Rate Limit]: Hết quota tạm thời. Đợi {wait_s}s rồi gọi lại API thật...")
                time.sleep(wait_s)
                try:
                    from google import genai
                    from google.genai import types
                    client = genai.Client(api_key=self.api_key)
                    function_declarations = []
                    for tool in tools_schema:
                        if not tool.get("name") or not tool.get("parameters"):
                            continue
                        function_declarations.append({
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {})
                        })
                    config = types.GenerateContentConfig(
                        system_instruction=system_prompt if system_prompt else None,
                        tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                        temperature=0.2
                    )
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config
                    )
                    if response.function_calls:
                        call = response.function_calls[0]
                        args = dict(call.args) if hasattr(call, "args") and call.args else {}
                        return {
                            "type": "tool_call",
                            "tool_name": call.name,
                            "arguments": args,
                            "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                        }
                    return {
                        "type": "text",
                        "content": response.text or "",
                        "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                    }
                except Exception as retry_err:
                    print(f"⚠️ [Gemini API Warning]: Retry thất bại ({str(retry_err)}). Tự động fallback về Mock.")
                    return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({err}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
