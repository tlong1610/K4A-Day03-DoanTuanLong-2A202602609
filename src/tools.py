"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Đề tài 3.2: Trợ lý Đơn hàng & Kho vận (Supply Chain Agent)
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu mã vận đơn + vị trí lưu kho
    {
        "name": "track_shipment",
        "description": (
            "Tra cứu đơn hàng theo mã vận đơn: thông tin khách hàng, hàng hóa, "
            "vị trí lưu kho (kho / dãy / ô) và trạng thái vận chuyển hiện tại."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_code": {
                    "type": "string",
                    "description": "Mã vận đơn cần tra cứu (ví dụ: 'VD2609001')"
                }
            },
            "required": ["tracking_code"]
        }
    },

    # Tool 2: Cập nhật trạng thái đơn hàng (công cụ hành động)
    {
        "name": "update_order_status",
        "description": (
            "Cập nhật trạng thái đơn hàng/kho vận theo mã vận đơn "
            "(ví dụ: Chờ xuất kho, Đã xuất kho, Đang vận chuyển, Đã giao hàng)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_code": {
                    "type": "string",
                    "description": "Mã vận đơn cần cập nhật (ví dụ: 'VD2609001')"
                },
                "new_status": {
                    "type": "string",
                    "description": "Trạng thái mới của đơn hàng (ví dụ: 'Đã xuất kho', 'Đã giao hàng')"
                },
                "warehouse_location": {
                    "type": "string",
                    "description": "Vị trí kho xác nhận cập nhật (ví dụ: 'Kho Trung tâm Bắc Ninh')"
                }
            },
            "required": ["tracking_code", "new_status"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "VD2609001": {
        "order_id": "SO-2609-001",
        "customer": "Công ty TNHH VinFast Trading",
        "product": "Cụm pin VF8 Plus",
        "quantity": 20,
        "unit": "thùng",
        "warehouse": "Kho Trung tâm Bắc Ninh",
        "aisle": "A-12",
        "bin": "B-07",
        "status": "Đang vận chuyển",
        "carrier": "VinLogistics",
        "eta": "15/09/2026",
        "last_update": "13/09/2026 08:30"
    },
    "VD2609002": {
        "order_id": "SO-2609-002",
        "customer": "VinFast Hải Phòng Showroom",
        "product": "Lốp xe VF9 kích thước 20 inch",
        "quantity": 80,
        "unit": "cái",
        "warehouse": "Kho Linh kiện Hải Phòng",
        "aisle": "C-04",
        "bin": "D-19",
        "status": "Chờ xuất kho",
        "carrier": "VinLogistics",
        "eta": "16/09/2026",
        "last_update": "12/09/2026 16:45"
    },
    "VD2609003": {
        "order_id": "SO-2609-003",
        "customer": "VinFast Đà Nẵng Service",
        "product": "Bộ sạc nhanh 11kW",
        "quantity": 12,
        "unit": "bộ",
        "warehouse": "Kho Miền Trung Đà Nẵng",
        "aisle": "E-02",
        "bin": "A-03",
        "status": "Đã giao hàng",
        "carrier": "VinLogistics Express",
        "eta": "10/09/2026",
        "last_update": "10/09/2026 11:20"
    }
}


def execute_track_shipment(tracking_code: str) -> str:
    """Thực thi tra cứu mã vận đơn và vị trí lưu kho"""
    order = MOCK_DATABASE.get(tracking_code.strip().upper())
    if order:
        return json.dumps({
            "status": "SUCCESS",
            "tracking_code": tracking_code.strip().upper(),
            "data": order
        }, ensure_ascii=False)
    return json.dumps({
        "status": "NOT_FOUND",
        "message": f"Không tìm thấy đơn hàng có mã vận đơn '{tracking_code}'."
    }, ensure_ascii=False)


def execute_update_order_status(
    tracking_code: str,
    new_status: str,
    warehouse_location: str = ""
) -> str:
    """Thực thi cập nhật trạng thái đơn hàng"""
    code = tracking_code.strip().upper()
    order = MOCK_DATABASE.get(code)
    if not order:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không thể cập nhật vì không tìm thấy mã vận đơn '{tracking_code}'."
        }, ensure_ascii=False)

    previous_status = order["status"]
    order["status"] = new_status
    if warehouse_location:
        order["warehouse"] = warehouse_location
    order["last_update"] = "13/09/2026 10:15"

    return json.dumps({
        "status": "SUCCESS",
        "update_id": f"UPD-{code}-99",
        "tracking_code": code,
        "order_id": order["order_id"],
        "previous_status": previous_status,
        "new_status": new_status,
        "warehouse": order["warehouse"],
        "message": (
            f"Đã cập nhật đơn {code} từ '{previous_status}' sang '{new_status}' "
            f"tại {order['warehouse']}."
        )
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "track_shipment": execute_track_shipment,
    "update_order_status": execute_update_order_status
}


def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
