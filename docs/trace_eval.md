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

Đã chạy `python src/app.py --all` với **`GeminiProvider` / `gemini-3.6-flash`**. Provider in ra `🔌 LLM Provider: GeminiProvider`. Thought có tiền tố *Gemini quyết định / Gemini phản hồi*, `latency_ms` khác 0 (khoảng 2–7 giây mỗi bước, không phải Mock). Đoạn dưới lấy **TC04** — chuỗi ReAct đa bước: Thought → Action `track_shipment` → Observation `Chờ xuất kho` → Action `update_order_status` → Final Answer.

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
    "latency_ms": 2572.03
  },
  {
    "step": 2,
    "query": "Tra cứu vị trí lưu kho của đơn VD2609002. Nếu đơn còn đang chờ xuất kho thì cập nhật trạng thái thành 'Đã xuất kho'.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "update_order_status",
    "arguments": {
      "new_status": "Đã xuất kho",
      "warehouse_location": "Kho Linh kiện Hải Phòng",
      "tracking_code": "VD2609002"
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
    "latency_ms": 3756.8
  },
  {
    "step": 4,
    "query": "Tra cứu vị trí lưu kho của đơn VD2609002. Nếu đơn còn đang chờ xuất kho thì cập nhật trạng thái thành 'Đã xuất kho'.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Thông tin tra cứu đơn hàng VD2609002: Kho Linh kiện Hải Phòng, dãy C-04, ô D-19. Trạng thái hiện tại: Đã xuất kho.",
    "latency_ms": 6234.94
  }
]
```

**Chuỗi ReAct quan sát được trên 5 test cases (Gemini API thật):**

| Test Case | Câu hỏi (ý) | Tool đã gọi | Kết quả quan sát | latency_ms (bước chính) |
| :--- | :--- | :--- | :--- | ---: |
| TC01 | Quy trình kho vận chuẩn? | Không gọi Tool | Gemini trả lời trực tiếp từ System Prompt. | 7129.57 |
| TC02 | Tra cứu `VD2609001` | `track_shipment` | SUCCESS — Kho Trung tâm Bắc Ninh, dãy A-12, ô B-07, đang vận chuyển. | 2410.94 |
| TC03 | Cập nhật `VD2609001` → Đã giao hàng | `update_order_status` | SUCCESS — đổi từ `Đang vận chuyển` sang `Đã giao hàng`, có `update_id`. | 2894.45 |
| TC04 | Tra cứu `VD2609002` rồi xuất kho nếu đủ điều kiện | `track_shipment` → `update_order_status` | Observation `Chờ xuất kho` quyết định bước cập nhật. | 2572.03 → 3756.80 |
| TC05 | Tra cứu `VD9999999` | `track_shipment` | NOT_FOUND — Gemini thông báo không tìm thấy, không bịa đơn hàng. | 2041.24 |

File log đầy đủ: `docs/trace_waterfall.json` (14 sự kiện, toàn bộ Thought ghi nhận phản hồi Gemini).

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` (`LLM_PROVIDER=gemini`, model `gemini-3.6-flash`) và xác nhận Agent chạy trên **GeminiProvider** (không còn `[Mock Agent Response]`, `latency_ms` khác 0).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server:** 9 lượt trên API thật (`track_shipment` + `update_order_status`). Chuỗi nghiệp vụ đúng kỳ vọng: TC02 tra cứu, TC03 cập nhật, TC04 tra cứu rồi cập nhật, TC05 `NOT_FOUND`.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân: https://github.com/tlong1610/K4A-Day03-DoanTuanLong-2A202602609

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
