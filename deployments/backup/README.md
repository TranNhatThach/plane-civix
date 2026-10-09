# 🛡️ CẨM NANG HỆ THỐNG SAO LƯU & KHÔI PHỤC DỮ LIỆU (PLANE-CIVIX DATABASE BACKUP)

Tài liệu này hướng dẫn chi tiết quy trình vận hành, tự động sao lưu, khôi phục và tải dữ liệu PostgreSQL dành cho quản trị viên và đội ngũ kỹ thuật tiếp quản hệ thống **Plane-Civix**.

---

## 📌 1. TỔNG QUAN KIẾN TRÚC SAO LƯU 2 TẦNG (TWO-TIER ARCHITECTURE)

Hệ thống Plane-Civix triển khai kiến trúc sao lưu 2 tầng bảo vệ dữ liệu toàn diện:

### 🌐 Tầng 1: Sao lưu toàn cục thực thể (Full Database Snapshot)

- **Loại Database:** PostgreSQL 15 (chạy trong Docker container `plane-db`).
- **Thư mục lưu:** `~/plane-backups/data/`
- **Định dạng:** `plane_backup_YYYYMMDD_HHMMSS.sql.gz` (nén gzip, có kiểm tra hash & khóa flock).
- **Chu kỳ:** Mỗi **60 phút** một lần (`0 * * * *`).
- **Chính sách lưu:** Giữ **30 ngày** gần nhất (~720 bản backup). Phục vụ khôi phục toàn bộ máy chủ VPS khi xảy ra sự cố phần cứng.

### 🏢 Tầng 2: Sao lưu phân lập theo Workspace (Isolated Per-Workspace Backup)

- **Cơ chế:** Quét và đóng gói toàn bộ bảng và dữ liệu nghiệp vụ của riêng từng Workspace thành file nén `.jsonl.gz`.
- **Thư mục lưu:** `~/plane-backups/workspaces/<workspace_id>/`
- **Chu kỳ tự động:** Hằng ngày lúc **02:00 sáng (giờ VN)** qua Celery Beat.
- **Chính sách lưu:** Giữ tối đa **45 bản mới nhất** cho mỗi workspace (tự động xóa bản cũ khi vượt quá).
- **Đặc tính độc lập:** Khi khôi phục dữ liệu cho 1 khách hàng (ví dụ: TID TECH), dữ liệu của CIVIX và các khách hàng khác **hoàn toàn không bị ảnh hưởng hay thụt lùi**.
- **Quản trị trực quan:** Xem, tải về, tạo ngay và khôi phục trực tiếp tại giao diện God-Mode: `/workspace/backups/`.
- **Thùng rác 15 ngày:** Workspace khi bị xóa sẽ được lưu trữ tạm trong 15 ngày, tự động tạo snapshot `pre-delete`, cho phép God-mode khôi phục trước khi xóa hẳn.

---

## 🚀 2. BỘ CÔNG CỤ SAO LƯU (DEPLOYMENTS/BACKUP/)

Trong thư mục `deployments/backup/` của dự án đã tích hợp sẵn trọn bộ script tự động:

| Tên File Script / Lệnh CLI     | Mục Đích Sử Dụng                                                         |
| :----------------------------- | :----------------------------------------------------------------------- |
| `setup_cron.sh`                | Cài đặt / Cập nhật tiến trình tự động sao lưu định kỳ (Crontab) trên VPS |
| `backup.sh`                    | Kích hoạt sao lưu toàn cục ngay lập tức & tự dọn dẹp file cũ > 30 ngày   |
| `get_download_link.sh`         | Menu chọn bản backup bất kỳ để sinh link tải trực tiếp (tự hủy sau 1h)   |
| `restore.sh`                   | Trình hướng dẫn an toàn 1-Click khôi phục database toàn cục              |
| `download_latest.ps1`          | Script PowerShell cho máy Windows tải bản backup mới nhất qua SSH/SCP    |
| `download_latest.sh`           | Script Shell cho máy Linux/Mac tải bản backup mới nhất qua SSH/SCP       |
| `civix_workspace_backup` (CLI) | Lệnh Django CLI quản lý sao lưu / khôi phục riêng từng workspace         |

---

## ⚙️ 3. HƯỚNG DẪN VẬN HÀNH TRÊN VPS

> **Đường dẫn thư mục dự án trên VPS:**  
> `cd ~/projects/misty-jade-0e49/plane-app/plane-civix`

### Bước 1: Kích hoạt tự động sao lưu định kỳ (Chỉ cần chạy 1 lần)

```bash
bash deployments/backup/setup_cron.sh
```

_(Mặc định chạy mỗi 60 phút và lưu 30 ngày. Nếu muốn đổi sang 30 phút/lần thì gõ `bash deployments/backup/setup_cron.sh 30`)._

### Bước 2: Tạo bản sao lưu ngay lập tức (Thủ công)

Khi chuẩn bị nâng cấp hệ thống, sửa code hoặc migration:

```bash
bash deployments/backup/backup.sh
```

Nếu muốn vừa tạo backup vừa in link tải về máy luôn:

```bash
bash deployments/backup/backup.sh --link
```

### Bước 3: Lấy link tải bản backup về máy tính

Khi đang ngồi ở máy khác qua SSH hoặc muốn tải file về máy cá nhân:

```bash
bash deployments/backup/get_download_link.sh
```

- Màn hình sẽ liệt kê danh sách 15 bản backup gần nhất kèm ngày giờ, dung lượng.
- Bấm **Enter** để chọn bản mới nhất `[1]` hoặc gõ số thứ tự mong muốn.
- Hệ thống sẽ trả về 1 đường link tải trực tiếp (link này tự động xóa sau 60 phút để bảo mật). Bạn chỉ cần dán vào trình duyệt máy tính để tải về.

### Bước 4: Khôi phục dữ liệu (Restore) khi có sự cố

Nếu hệ thống gặp lỗi hoặc muốn quay lại dữ liệu quá khứ:

```bash
bash deployments/backup/restore.sh
```

- Chọn số thứ tự bản sao lưu muốn khôi phục.
- Xác nhận `y`. Hệ thống sẽ tự động nạp lại toàn bộ dữ liệu chỉ trong vài giây.

---

## 📥 4. HƯỚNG DẪN TẢI VỀ MÁY TÍNH CÁ NHÂN

### Cách 1: Dùng script `download_latest.ps1` (Trên máy tính Windows)

Mở PowerShell tại thư mục code trên máy tính của bạn:

```powershell
powershell -ExecutionPolicy Bypass -File deployments/backup/download_latest.ps1 root@<IP_VPS>
```

File backup sẽ được tự động lưu vào `D:\Backup\` (hoặc `.\backups`).

### Cách 2: Dùng SCP truyền thống

```powershell
scp root@<IP_VPS>:~/plane-backups/data/*.sql.gz D:\Backup\
```

---

## 🔒 5. NGUYÊN TẮC BẢO MẬT & BẢO TRÌ

1. **Kiểm tra dung lượng định kỳ:** Lệnh `du -sh ~/plane-backups/data/` để kiểm tra tổng dung lượng thư mục backup.
2. **File copy tạm:** Sau khi copy file thủ công ra ngoài thư mục project, luôn nhớ xóa file tạm: `rm -f ./latest_backup.sql.gz`.
3. **Bản quyền & Chuẩn Civix:** Mọi thay đổi logic liên quan đến sao lưu và bảo mật phiên đăng nhập đều được đồng bộ tại Cổng Changelog & Docs Portal `/changelog` ([`apps/web/core/data/civix-docs.json`](../apps/web/core/data/civix-docs.json)).
