---
name: civix
description: >-
  Cẩm nang quy chuẩn làm việc, quy trình phát triển phần mềm, chuẩn viết tài liệu (Documentation),
  chuẩn viết nhật ký phiên bản (Changelog & Release Notes), và vận hành hệ thống AI Agent / Slack / Telegram Bot cho dự án Civix.
---

# 🏢 Cẩm Nang Chuẩn Mực Làm Việc & Quy Trình Phát Triển Civix (.Civix)

Tài liệu này định hình **văn hóa công sở, quy chuẩn kỹ thuật, quy trình phát hành phiên bản và chuẩn viết tài liệu** dành riêng cho đội ngũ phát triển và quản trị hệ thống **Plane-Civix**.

---

## 🧭 1. Triết Lý & Thói Quen Làm Việc Công Sở (Workplace Habits)

### 🤝 Minh bạch & Giao tiếp (Communication)

- **Cập nhật tiến độ rõ ràng**: Mọi thay đổi lớn, tính năng mới hoặc bản vá lỗi phải được ghi chú trong **Changelog** và cập nhật trạng thái trên Plane Issues.
- **Thân thiện với người dùng phi kỹ thuật & Cấp quản lý**: Khi viết tài liệu hoặc thông báo cập nhật cho Sếp, sử dụng văn phong súc tích, trực quan, có gạch đầu dòng rõ ràng, giải thích ngắn gọn lợi ích thay vì chỉ liệt kê code.
- **Chủ động thử nghiệm & Tự kiểm thử (Self-testing)**: Luôn chạy lint (`pnpm check:lint`) và test suite trước khi bàn giao sản phẩm.

### 🌿 Quy chuẩn Git & Nhánh (Branching & Commits)

- **Cấu trúc nhánh (Branching)**:
  - `main`: Nhánh production ổn định.
  - `develop`: Nhánh tích hợp chính.
  - `feature/<ten-tinh-nang>`: Nhánh phát triển tính năng mới.
  - `bugfix/<ten-loi-can-sua>`: Nhánh sửa lỗi.
  - `release/vX.Y.Z`: Nhánh chuẩn bị đóng gói phát hành phiên bản.
- **Quy chuẩn Commit Message (Conventional Commits)**:
  - `feat(agent): thêm tính năng tra cứu changelog qua Slack Bot`
  - `fix(auth): sửa lỗi routing nhầm workspace cá nhân khi sếp gọi /agent`
  - `docs(changelog): cập nhật release notes cho phiên bản v1.4.1`
  - `perf(engine): tối ưu fast-path matcher phản hồi dưới 50ms`
  - `refactor(context): tái cấu trúc ContextResolver bảo mật theo membership`

---

## 📝 2. Quy Chuẩn Viết Tài Liệu Hướng Dẫn (Documentation Standard)

Mỗi tài liệu hướng dẫn tính năng mới hoặc tài liệu kỹ thuật trong Civix cần tuân thủ cấu trúc 5 phần:

```markdown
# [Tên Tính Năng / Hướng Dẫn]

## 1. 📌 Tổng Quan (Overview)

- Mục đích của tính năng là gì? Giải quyết bài toán gì cho team/công ty?
- Đối tượng sử dụng (Sếp, Project Manager, Developer, Thành viên).

## 2. ⚙️ Yêu Cầu & Chuẩn Bị (Prerequisites)

- Cần quyền hạn gì trong Workspace (Admin / Member)?
- Cần cấu hình gì trước (Bot Token, API Key,...)?

## 3. 🚀 Hướng Dẫn Từng Bước (Step-by-Step Guide)

- Bước 1: ...
- Bước 2: ... (Kèm hình ảnh minh họa / ví dụ câu lệnh cụ thể)

## 4. 💡 Mẹo & Phím Tắt Tiện Ích (Tips & Best Practices)

- Các mẹo giúp thao tác nhanh hơn.

## 5. ❓ Câu Hỏi Thường Gặp & Xử Lý Sự Cố (FAQ & Troubleshooting)

- Các lỗi thường gặp và cách khắc phục nhanh chóng.
```

---

## 📋 3. Quy Chuẩn Viết Nhật Ký Phiên Bản (Changelog & Release Notes)

### 🏷️ Quy tắc đặt số phiên bản (Semantic Versioning - SemVer)

Định dạng: **`vMAJOR.MINOR.PATCH`** (Ví dụ: `v1.4.1`)

- **`MAJOR` (1.x.x)**: Thay đổi kiến trúc lớn, nâng cấp framework cốt lõi (e.g. Django 5.2, React Router v7).
- **`MINOR` (x.4.x)**: Thêm tính năng mới lớn (e.g. Slack Socket Mode Agent, Telegram Multi-Project Sync).
- **`PATCH` (x.x.1)**: Vá lỗi (Bug fixes), tối ưu hiệu năng nhỏ, tinh chỉnh giao diện.

### 🎨 Cấu trúc chuẩn của một bản Release Note

Mỗi phiên bản trong Changelog phải được nhóm thành 5 nhóm biểu tượng:

1. 🚀 **What's New (Tính năng mới)**: Những tính năng vừa được bổ sung.
2. 🐛 **Bug Fixes (Lỗi đã khắc phục)**: Ghi rõ lỗi gì đã được xử lý, mã issue (nếu có) và tác động tích cực sau khi fix.
3. ⚡ **Performance & UX (Cải tiến hiệu năng & Trải nghiệm)**: Tốc độ xử lý, giao diện mượt hơn.
4. 🤖 **AI Agent & Bots (Nâng cấp Agent)**: Các lệnh mới trên Slack/Telegram, khả năng phân tích của AI.
5. 🔒 **Security & Permissions (Bảo mật & Phân quyền)**: Cập nhật quyền hạn, phân lập dữ liệu giữa các workspace.

---

## 🤖 4. Quy Chuẩn Vận Hành AI Agent & Bot (Slack / Telegram)

1. **Nguyên tắc Phân Lập Workspace (Workspace Isolation)**:
   - Bot chỉ được phép truy vấn dữ liệu từ **Workspace công ty** có kết nối tích hợp hợp lệ.
   - Tuyệt đối không để rò rỉ dữ liệu giữa các Workspace cá nhân và Workspace công ty.
2. **Nguyên tắc Xác Thực Danh Tính (Identity First)**:
   - Phải map chính xác User Slack qua Email hoặc `SlackUserIntegration`. Nếu không xác thực được, trả về thông báo hướng dẫn thay vì tự gán sang người khác.
3. **Cơ chế An Toàn HITL (Human-In-The-Loop)**:
   - Các hành động ghi/sửa dữ liệu quan trọng (như tự động rebalance workload, tạo hàng loạt task) phải có nút bấm xác nhận `[Xác nhận]` / `[Hủy]` trước khi thực thi.
