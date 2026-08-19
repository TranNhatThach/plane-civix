# 📋 Lịch Sử Phiên Bản & Nhật Ký Phát Triển Civix (Changelog)

Toàn bộ lịch sử các bản phát hành, tính năng mới và danh sách các lỗi (bugs) đã được khắc phục qua từng phiên bản của dự án **Plane-Civix**.

---

## 🚀 [v1.4.1] — 19/08/2026 _(Bản mới nhất)_

### 🛡️ Bảo Mật Định Tuyến Slack Workspace & Hệ Thống Changelog / Skill .Civix

- **Tóm tắt**: Khắc phục triệt để lỗi định tuyến nhầm vào Workspace cá nhân khi sử dụng lệnh `/agent` từ Slack; ra mắt cổng tra cứu Documentation & Changelog chuyên biệt cùng bộ cẩm nang Skill `.Civix`.
- **🐛 Bug Fixes**:
  - Sửa lỗi Slack Agent gọi nhầm Workspace cá nhân thay vì Workspace công ty.
  - Xóa bỏ cơ chế fallback mù quáng về User #1 trong database; bắt buộc xác thực User qua Email/ID.
- **✨ Features**:
  - Cổng tra cứu Documentation & Changelog chuyên biệt tại đường dẫn `/changelog`.
  - Bộ cẩm nang quy chuẩn làm việc và văn hóa công sở Skill `.Civix`.
- **🤖 AI Agent & Bot Updates**:
  - Tích hợp tool `tool_get_changelog` cho phép sếp gõ `/agent changelog` trực tiếp trên Slack.
  - Bổ sung tin nhắn hướng dẫn phân quyền chi tiết kèm Slack User ID khi user chưa được cấp quyền.

---

## 🚀 [v1.4.0] — 17/08/2026

### 📦 Trello Board Importer, AIMarkdownRenderer & AI Gateway Provider

- **Tóm tắt**: Tích hợp công cụ nhập dữ liệu từ Trello Board, trình render Markdown tối ưu hóa cho AI không phụ thuộc thư viện ngoài, hỗ trợ AI Gateway tùy biến và hệ thống sao lưu tự động 5 phút.
- **✨ Features**:
  - Bộ nhập dữ liệu Trello Board JSON (Trello Importer) tự động ánh xạ trạng thái và nhãn.
  - Trình hiển thị `AIMarkdownRenderer` độc quyền zero-dependency (copy code 1 chạm, bảng biểu, typography).
  - Bộ sao lưu dữ liệu tự động PostgreSQL định kỳ 5 phút (`5-min backup suite`).
- **🤖 AI Agent Updates**:
  - Civix Custom AI Gateway Provider kết nối DeepSeek, Gemini 2.0, OpenRouter và vượt qua tường lửa WAF.
  - Bảng điều khiển AI Agent & Harness controls trong Admin UI.

---

## 🚀 [v1.3.5] — 12/08/2026

### ⚡ Slack Socket Mode, Fast-Path Engine & Phê Duyệt An Toàn HITL

- **Tóm tắt**: Kết nối Slack Bot thời gian thực qua Socket Mode an toàn trong mạng nội bộ, thiết kế Block Kit tương tác cao và cơ chế kiểm soát Human-In-The-Loop.
- **✨ Features**:
  - Kết nối Slack Socket Mode thời gian thực không cần Public IP.
  - Thẻ thông tin tương tác Slack Block Kit Card 2 cột với thanh tiến độ visual.
  - Lệnh tra cứu nhanh `/agent myid`.
- **⚡ Performance & AI Updates**:
  - Fast-Path Engine phản hồi các truy vấn xem tiến độ/task dưới 50ms.
  - Cơ chế Human-In-The-Loop (HITL) tạo nút [Xác nhận] / [Hủy] khi Agent đề xuất phân bổ lại công việc.

---

## 🚀 [v1.3.0] — 05/08/2026

### 💬 Telegram Bot Tương Tác 2 Chiều, Tự Hủy Tin Nhắn & Đa Dự Án

- **Tóm tắt**: Nâng cấp toàn diện Telegram Bot hỗ trợ đàm thoại 2 chiều, tạo task tự động bằng AI, tự xóa tin nhắn sau 45s và quản lý nhiều dự án trong cùng một nhóm.
- **✨ Features**:
  - Telegram Bot tương tác 2 chiều với chế độ AI Q&A và tạo task thông minh.
  - Form cấu hình `TelegramIntegrationForm` trong Workspace Settings.
- **⚡ Improvements & Bug Fixes**:
  - Tính năng tự hủy tin nhắn (Self-destruct messages) sau 45 giây chống loãng nhóm chat.
  - Sửa lỗi trùng lặp tin nhắn Webhook trên Telegram khi mạng chập chờn.

---

## 🚀 [v1.2.0] — 20/07/2026

### 🏗️ Nâng Cấp Kiến Trúc Django 5.2 LTS & React Router v7 Vite

- **Tóm tắt**: Hiện đại hóa nền tảng kỹ thuật với Django 5.2 LTS (Python 3.13), React Router v7 trên nền Vite và mở rộng hỗ trợ nhiều nhà cung cấp AI tiên tiến.
- **⚡ Improvements**:
  - Nâng cấp Backend lên Django 5.2 LTS, tăng tốc độ xử lý ORM PostgreSQL.
  - Frontend hiện đại với React Router v7 & Vite, tăng tốc độ tải trang gấp 2.5 lần.
  - Cho phép thành viên Workspace xem các dự án công khai (Public Projects) không cần invite thủ công.
