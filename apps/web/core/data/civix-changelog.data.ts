/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

export interface IChangelogItem {
  type: "feature" | "fix" | "improvement" | "agent" | "security";
  title: string;
  description?: string;
  issueKey?: string;
}

export interface IReleaseChangelog {
  version: string;
  title: string;
  releaseDate: string;
  badgeText?: string;
  isLatest?: boolean;
  summary: string;
  highlights?: string[];
  items: IChangelogItem[];
}

export const CIVIX_CHANGELOG_RELEASES: IReleaseChangelog[] = [
  {
    version: "v1.4.1",
    title: "Bảo Mật Định Tuyến Slack Workspace & Hệ Thống Changelog / Skill .Civix",
    releaseDate: "19/08/2026",
    badgeText: "Bản Mới Nhất",
    isLatest: true,
    summary:
      "Khắc phục triệt để lỗi định tuyến nhầm vào Workspace cá nhân khi sử dụng lệnh /agent từ Slack; ra mắt cổng tra cứu Documentation & Changelog chuyên biệt cùng bộ cẩm nang quy chuẩn làm việc Skill .Civix.",
    highlights: [
      "Khắc phục lỗi Agent bốc nhầm Workspace cá nhân khi sếp gõ lệnh trên Slack",
      "Xóa bỏ cơ chế Fallback mù quáng về User #1 trong ContextResolver",
      "Tự động map danh tính Slack User với Plane User qua Email an toàn",
      "Ra mắt trang Changelog Timeline chuyên biệt (/changelog) chuẩn phong cách Docs",
      "Tích hợp tra cứu phiên bản & bug fixes trực tiếp qua lệnh /agent trên Slack",
      "Ban hành bộ cẩm nang văn hóa công sở và quy chuẩn kỹ thuật Skill .Civix",
    ],
    items: [
      {
        type: "fix",
        title: "Sửa lỗi Slack Agent gọi nhầm Workspace cá nhân thay vì Workspace công ty",
        description:
          "Ràng buộc bắt buộc Workspace được chọn phải có cấu hình SlackAutomation đang active và user gọi lệnh phải là thành viên hợp lệ (WorkspaceMember / ProjectMember).",
      },
      {
        type: "security",
        title: "Nâng cấp xác thực danh tính an toàn (Identity First)",
        description:
          "Loại bỏ hoàn toàn cơ chế tự động gán user lạ sang tài khoản đầu tiên trong database. Trả về thông báo lỗi hướng dẫn cấp quyền rõ ràng kèm Slack User ID.",
      },
      {
        type: "feature",
        title: "Cổng Documentation & Changelog chuyên biệt cho Civix (/changelog)",
        description:
          "Giao diện timeline trực quan với bộ lọc tags (Bug fixes, Tính năng mới, AI Agent, Bảo mật) và ô tìm kiếm từ khóa thời gian thực.",
      },
      {
        type: "agent",
        title: "Tích hợp tool tra cứu Changelog vào Slack AI Agent",
        description:
          "Cho phép sếp và các thành viên gõ '/agent có cập nhật gì mới không' hoặc '/agent các bug đã fix' để nhận tóm tắt phiên bản ngay lập tức.",
      },
      {
        type: "improvement",
        title: "Bộ cẩm nang quy chuẩn làm việc và văn hóa công sở Skill .Civix",
        description:
          "Định nghĩa chuẩn viết tài liệu 5 phần, chuẩn viết release notes SemVer, quy ước Git commit và nguyên tắc vận hành an toàn cho AI Agent.",
      },
    ],
  },
  {
    version: "v1.4.0",
    title: "Trello Board Importer, AIMarkdownRenderer & AI Gateway Provider",
    releaseDate: "17/08/2026",
    summary:
      "Tích hợp công cụ nhập dữ liệu từ Trello Board, trình render Markdown tối ưu hóa cho AI không phụ thuộc thư viện ngoài, hỗ trợ AI Gateway tùy biến và hệ thống sao lưu tự động 5 phút.",
    highlights: [
      "Công cụ Trello Board Importer nhập dữ liệu kèm ánh xạ tự động trạng thái & nhãn",
      "AIMarkdownRenderer độc quyền hỗ trợ copy code block, bảng biểu và typography",
      "Hỗ trợ Civix Custom AI Gateway Provider (DeepSeek, Gemini, OpenRouter)",
      "Bộ công cụ sao lưu dữ liệu tự động mỗi 5 phút (5-min automated backup suite)",
    ],
    items: [
      {
        type: "feature",
        title: "Bộ nhập dữ liệu Trello Board JSON (Trello Importer)",
        description:
          "Cho phép tải lên tệp JSON xuất từ Trello, tự động chuyển đổi danh sách thành trạng thái (States), thẻ (Labels), mô tả và phân công thành viên trong Plane.",
      },
      {
        type: "improvement",
        title: "Trình hiển thị AIMarkdownRenderer độc quyền",
        description:
          "Thiết kế zero-dependency tương thích hoàn hảo với production bundler, hỗ trợ nút sao chép code 1 chạm, bảng biểu dữ liệu và giao diện Dark/Light mượt mà.",
      },
      {
        type: "agent",
        title: "Civix Custom AI Gateway Provider & Bypass WAF",
        description:
          "Hỗ trợ kết nối các mô hình ngôn ngữ lớn qua Custom Base URL, tự động xử lý User-Agent để tránh bị tường lửa Cloudflare/WAF chặn kết nối.",
      },
      {
        type: "security",
        title: "Bộ sao lưu dữ liệu tự động định kỳ 5 phút",
        description:
          "Tự động xuất bản sao lưu PostgreSQL an toàn vào thư mục lưu trữ, hỗ trợ script phục hồi dữ liệu tương tác không cần nhập mật khẩu thủ công.",
      },
    ],
  },
  {
    version: "v1.3.5",
    title: "Slack Socket Mode, Fast-Path Engine & Phê Duyệt An Toàn HITL",
    releaseDate: "12/08/2026",
    summary:
      "Kết nối Slack Bot thời gian thực qua Socket Mode an toàn trong mạng nội bộ, thiết kế Block Kit tương tác cao và cơ chế kiểm soát Human-In-The-Loop.",
    highlights: [
      "Kết nối Slack Socket Mode thời gian thực không cần mở port Public IP",
      "Giao diện thẻ Block Kit 2 cột trực quan với visual progress bar",
      "Fast-Path Pattern Matcher phản hồi truy vấn dưới 50ms",
      "Cơ chế Human-In-The-Loop: Nút [Xác nhận] / [Hủy] điều chuyển công việc",
    ],
    items: [
      {
        type: "agent",
        title: "Hỗ trợ kết nối Socket Mode cho Slack Bot",
        description:
          "Chạy bot trực tiếp trong mạng doanh nghiệp với Bot Token & App Token (xapp-), loại bỏ hoàn toàn sự phụ thuộc vào Ngrok hay Public Webhook IP.",
      },
      {
        type: "feature",
        title: "Thẻ thông tin tương tác Slack Block Kit Card",
        description:
          "Trình bày báo cáo tiến độ trực quan với thanh % hoàn thành, bảng phân bổ công việc thành viên và các nút hành động xem nhanh trên Web.",
      },
      {
        type: "improvement",
        title: "Fast-Path Engine xử lý siêu tốc (<50ms)",
        description:
          "Tự động nhận diện ý định và truy vấn trực tiếp cơ sở dữ liệu cho các lệnh xem tiến độ, danh sách task mà không cần chờ LLM xử lý.",
      },
      {
        type: "agent",
        title: "Cơ chế phê duyệt Human-In-The-Loop (HITL)",
        description:
          "Khi Agent đề xuất tái phân bổ task trễ hạn (Workload Rebalance), hệ thống sẽ gửi nút xác nhận trước khi thực hiện thay đổi dữ liệu.",
      },
    ],
  },
  {
    version: "v1.3.0",
    title: "Telegram Bot Tương Tác 2 Chiều, Tự Hủy Tin Nhắn & Đa Dự Án",
    releaseDate: "05/08/2026",
    summary:
      "Nâng cấp toàn diện Telegram Bot hỗ trợ đàm thoại 2 chiều, tạo task tự động bằng AI, tự xóa tin nhắn sau 45s và quản lý nhiều dự án trong cùng một nhóm.",
    highlights: [
      "Telegram Bot tương tác 2 chiều với chế độ AI Q&A",
      "Tính năng tự hủy tin nhắn (Self-destruct messages) sau 45s",
      "Hỗ trợ quản lý đa dự án linh hoạt trong cùng nhóm Telegram",
      "Form cấu hình TelegramIntegrationForm trong Workspace Settings",
    ],
    items: [
      {
        type: "feature",
        title: "Tạo task và hỏi đáp thông minh qua Telegram Bot",
        description:
          "Thành viên có thể gửi tin nhắn tự nhiên vào nhóm Telegram để Bot tự động tạo công việc và gán nhãn chính xác.",
      },
      {
        type: "improvement",
        title: "Tự động dọn dẹp tin nhắn phản hồi (Self-Destruct)",
        description:
          "Tin nhắn kết quả của Bot sẽ tự động biến mất sau 45 giây để giữ cho luồng thảo luận của nhóm chat luôn gọn gàng.",
      },
      {
        type: "fix",
        title: "Sửa lỗi trùng lặp tin nhắn Webhook trên Telegram",
        description: "Thêm bộ nhớ đệm chống xử lý duplicate update ID khi đường truyền mạng chập chờn.",
      },
      {
        type: "feature",
        title: "Giao diện tích hợp Telegram trong Workspace Settings",
        description:
          "Cung cấp màn hình cấu hình Bot Token và Chat ID trực quan ngay trong mục Cài đặt tích hợp của Workspace.",
      },
    ],
  },
  {
    version: "v1.2.0",
    title: "Nâng Cấp Kiến Trúc Django 5.2 LTS & React Router v7 Vite",
    releaseDate: "20/07/2026",
    summary:
      "Hiện đại hóa nền tảng kỹ thuật với Django 5.2 LTS (Python 3.13), React Router v7 trên nền Vite và mở rộng hỗ trợ nhiều nhà cung cấp AI tiên tiến.",
    highlights: [
      "Nâng cấp Backend lên Django 5.2 LTS",
      "Chuyển đổi Frontend sang React Router v7 & Vite Build System",
      "Mở rộng hỗ trợ nhà cung cấp LLM (DeepSeek, Gemini 2.0, OpenAI)",
      "Quyền truy cập dự án công khai (Public Project Access) mượt mà",
    ],
    items: [
      {
        type: "improvement",
        title: "Nâng cấp Backend lên Django 5.2 LTS",
        description: "Tương thích với Python 3.13, tối ưu hóa các câu truy vấn ORM và cải thiện độ ổn định của API.",
      },
      {
        type: "improvement",
        title: "Frontend hiện đại với React Router v7 & Vite",
        description: "Tăng tốc độ khởi động trang web gấp 2.5 lần và giảm đáng kể dung lượng gói bundle khi tải trang.",
      },
      {
        type: "agent",
        title: "Mở rộng hệ sinh thái mô hình AI",
        description:
          "Hỗ trợ tích hợp DeepSeek-Chat/Coder, Google Gemini 2.0 Flash/Pro và các nhà cung cấp tương thích OpenAI.",
      },
      {
        type: "feature",
        title: "Cho phép thành viên Workspace xem dự án công khai (Public Projects)",
        description:
          "Thành viên hợp lệ trong Workspace có thể truy cập và xem các dự án công khai mà không bắt buộc phải gửi lời mời tham gia thủ công.",
      },
    ],
  },
];
