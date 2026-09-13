# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Đoàn Tuấn Long  
> **Mã Sinh Viên / Mã Học viên:** 2A202602609  
> **Chủ đề Lựa chọn:** Gợi ý 3.2 — Trợ lý Đơn hàng & Kho vận (Supply Chain Agent): Tra cứu mã vận đơn, vị trí lưu kho và cập nhật trạng thái đơn hàng.

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5 / 5 | Điều phối viên không hỏi một câu rồi xong. Luồng điển hình phải tách thành nhiều bước nối tiếp: (1) nhận mã vận đơn, (2) tra cứu vị trí kho và trạng thái hiện tại, (3) đối chiếu điều kiện (còn hàng / chờ xuất kho / đã giao), (4) mới cập nhật trạng thái. TC04 minh họa rõ: phải gọi `track_shipment` trước, đọc Observation, rồi mới quyết định gọi `update_order_status`. Không thể gộp thành một câu trả lời tĩnh. |
| **2. Tool Interaction** | 5 / 5 | Vị trí kệ (kho / dãy / ô) và trạng thái đơn thay đổi theo ca xuất nhập, không thể nhét vào System Prompt. Agent bắt buộc gọi MCP Server để đọc CSDL kho (`track_shipment`) và ghi hành động (`update_order_status`). Nếu không có Tool, mô hình sẽ ảo giác mã vận đơn, vị trí lưu kho và trạng thái. |
| **3. Dynamic Decision** | 5 / 5 | Bước kế tiếp phụ thuộc hoàn toàn vào Observation. Nếu Tool trả `SUCCESS` và trạng thái là `Chờ xuất kho` → được phép xuất kho. Nếu đơn đã `Đã giao hàng` → không xuất lại. Nếu `NOT_FOUND` (mã `VD9999999`) → dừng, thông báo lịch sự, tuyệt đối không bịa đơn. Nhánh quyết định này không thể hard-code trước khi thấy dữ liệu thật. |
| **4. Long Horizon Goal** | 4 / 5 | Mục tiêu xuyên suốt là hoàn tất vòng đời một đơn hàng (định vị hàng → xác nhận điều kiện → cập nhật trạng thái → phản hồi điều phối viên), không phải trả lời FAQ rồi quên ngữ cảnh. Agent phải giữ mã vận đơn, vị trí kho và trạng thái cũ qua nhiều lượt Tool. Chấm 4/5 vì phạm vi Lab chỉ mô phỏng 1–2 vòng ReAct, chưa có planning dài ngày hay bộ nhớ đa phiên. |
| **TỔNG ĐIỂM AGENTIC FIT** | **19 / 20** | *Tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System.* Chatbot thuần văn bản không đọc được tồn kho thật và không ghi được trạng thái đơn; cần ReAct Agent + MCP. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Đã chạy `python src/app.py --all`: **5/5 test cases** hoàn tất, ghi **10 sự kiện** vào `docs/trace_waterfall.json`. Đoạn dưới đây lấy **TC04** (case đa bước tiêu biểu): Agent gọi `track_shipment` trước, thấy trạng thái `Chờ xuất kho`, rồi mới gọi `update_order_status`.

```json
[
  {
    "step": 1,
    "query": "Tra cứu vị trí lưu kho của đơn VD2609002. Nếu đơn còn đang chờ xuất kho thì cập nhật trạng thái thành 'Đã xuất kho'.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "track_shipment",
    "arguments": {
      "tracking_code": "VD2609002"
    },
    "observation": {
      "status": "SUCCESS",
      "tracking_code": "VD2609002",
      "data": {
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
      }
    },
    "latency_ms": 0.0
  },
  {
    "step": 2,
    "query": "Tra cứu vị trí lưu kho của đơn VD2609002. Nếu đơn còn đang chờ xuất kho thì cập nhật trạng thái thành 'Đã xuất kho'.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "update_order_status",
    "arguments": {
      "tracking_code": "VD2609002",
      "new_status": "Đã xuất kho",
      "warehouse_location": "Kho Linh kiện Hải Phòng"
    },
    "observation": {
      "status": "SUCCESS",
      "update_id": "UPD-VD2609002-99",
      "tracking_code": "VD2609002",
      "order_id": "SO-2609-002",
      "previous_status": "Chờ xuất kho",
      "new_status": "Đã xuất kho",
      "warehouse": "Kho Linh kiện Hải Phòng",
      "message": "Đã cập nhật đơn VD2609002 từ 'Chờ xuất kho' sang 'Đã xuất kho' tại Kho Linh kiện Hải Phòng."
    },
    "latency_ms": 0.0
  },
  {
    "step": 3,
    "query": "Tra cứu vị trí lưu kho của đơn VD2609002. Nếu đơn còn đang chờ xuất kho thì cập nhật trạng thái thành 'Đã xuất kho'.",
    "action_type": "FINAL_ANSWER",
    "thought": "Đã nhận Observation, đưa ra câu trả lời cuối cùng.",
    "output": "Đã cập nhật đơn VD2609002 từ 'Chờ xuất kho' sang 'Đã xuất kho' tại Kho Linh kiện Hải Phòng.",
    "latency_ms": 0.0
  }
]
```

**Chuỗi ReAct quan sát được trên 5 test cases:**

| Test Case | Câu hỏi (ý) | Tool đã gọi | Kết quả quan sát |
| :--- | :--- | :--- | :--- |
| TC01 | Quy trình kho vận chuẩn? | Không gọi Tool | Trả lời trực tiếp từ System Prompt. |
| TC02 | Tra cứu `VD2609001` | `track_shipment` | SUCCESS — Kho Trung tâm Bắc Ninh, dãy A-12, ô B-07, đang vận chuyển. |
| TC03 | Cập nhật `VD2609001` → Đã giao hàng | `update_order_status` | SUCCESS — đổi từ `Đang vận chuyển` sang `Đã giao hàng`, có `update_id`. |
| TC04 | Tra cứu `VD2609002` rồi xuất kho nếu đủ điều kiện | `track_shipment` → `update_order_status` | Observation `Chờ xuất kho` quyết định bước cập nhật. |
| TC05 | Tra cứu `VD9999999` | `track_shipment` | NOT_FOUND — không bịa đơn hàng. |

File log đầy đủ: `docs/trace_waterfall.json`.

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [ ] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI). Lần chạy `python src/app.py --all` hiện tại dùng `MockOfflineProvider` (file `.env` trên đĩa vẫn là `your_gemini_api_key_here`). Cần **lưu key Gemini thật vào `.env`**, rồi chạy lại `python src/app.py --all` để `latency_ms` khác 0 trước khi nộp LMS.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt (`track_shipment` × 3 + `update_order_status` × 2).
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
