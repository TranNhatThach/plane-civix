/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

export interface IChangelogSectionDetail {
  id: string;
  title: string;
  body: string[];
  code?: string;
  callout?: {
    type: "tip" | "info" | "warning";
    text: string;
  };
}

export interface IChangelogSectionGroup {
  id: string;
  heading: "What's new" | "Enhancements" | "Bug fixes" | "AI Agent & Bots" | "Security & Permissions";
  items: IChangelogSectionDetail[];
}

export interface IReleaseChangelog {
  id: string;
  version: string;
  title: string;
  formattedDate: string; // e.g. "August 24, 2026"
  shortDate: string; // e.g. "24 Aug, 2026"
  category: "Cloud" | "Self-hosted" | "Mobile";
  badgeText?: string;
  isLatest?: boolean;
  summary: string;
  heroBannerTitle?: string;
  sections: IChangelogSectionGroup[];
}

export const CIVIX_CHANGELOG_RELEASES: IReleaseChangelog[] = [
  {
    id: "v1-4-2",
    version: "v1.4.2",
    title: "MinIO S3 Dynamic Host Storage, @civix.com.vn Whitelist & SMTP | Aug 24, 2026",
    formattedDate: "August 24, 2026",
    shortDate: "24 Aug, 2026",
    category: "Self-hosted",
    badgeText: "Bản Mới Nhất",
    isLatest: true,
    summary:
      "Tối ưu hóa toàn diện hạ tầng lưu trữ S3/MinIO với cơ chế tự động phân giải tên miền công khai cho Presigned URLs, đồng thời thiết lập chính sách bảo mật chỉ cho phép đăng ký tài khoản mới bằng email @civix.com.vn và kích hoạt gửi mail SMTP.",
    heroBannerTitle: "MinIO S3 Dynamic Host Storage, @civix.com.vn Whitelist & SMTP | Aug 24, 2026",
    sections: [
      {
        id: "whats-new",
        heading: "What's new",
        items: [
          {
            id: "minio-dynamic-host",
            title: "Hạ tầng lưu trữ MinIO S3 Dynamic Host Resolution",
            body: [
              "Tự động phát hiện tên miền người dùng đang truy cập (plane.civix.com.vn hoặc IP VPS) để sinh URL tải lên và URL xem ảnh chuẩn xác.",
              "Trình duyệt tải ảnh đại diện, ảnh bìa, tệp đính kèm và ảnh trong editor trực tiếp qua cổng 80/443 của Caddy mà không bị chặn CORS hay lỗi kết nối mạng.",
            ],
            callout: {
              type: "tip",
              text: "Tất cả ảnh đại diện (avatar), ảnh bìa (cover), tài liệu đính kèm task và ảnh trong trình soạn thảo đều được tải lên và hiển thị tức thì.",
            },
          },
          {
            id: "domain-whitelist",
            title: "Chính sách đăng ký tài khoản bảo mật @civix.com.vn",
            body: [
              "Chỉ cho phép tài khoản có đuôi email @civix.com.vn đăng ký mới vào hệ thống.",
              "Các tài khoản legacy đã tồn tại trước đó từ các nhà cung cấp khác vẫn tiếp tục đăng nhập và làm việc bình thường mà không bị gián đoạn.",
            ],
            code: '# Cấu hình SMTP gửi mail kích hoạt tài khoản trong apps/api/.env\nEMAIL_HOST="smtp.gmail.com"\nEMAIL_PORT=587\nEMAIL_USE_TLS=1',
          },
        ],
      },
      {
        id: "enhancements",
        heading: "Enhancements",
        items: [
          {
            id: "sigv4-matching",
            title: "Chữ ký AWS Signature V4 chuẩn Host công khai",
            body: [
              "Client Boto3 được khởi tạo trực tiếp với public endpoint giúp tính toán header Host đồng nhất giữa client và máy chủ MinIO.",
            ],
          },
          {
            id: "caddy-proxy-bypass",
            title: "Tối ưu hóa Caddy Reverse Proxy cho /uploads",
            body: ["Cấu hình proxy chuyển tiếp mượt mà /uploads/* trực tiếp vào container MinIO port 9000."],
          },
        ],
      },
      {
        id: "bug-fixes",
        heading: "Bug fixes",
        items: [
          {
            id: "fix-403-signature",
            title: "Khắc phục lỗi 403 SignatureDoesNotMatch khi xem ảnh",
            body: ["Loại bỏ việc thay thế chuỗi thủ công trên URL đã ký, đảm bảo toàn bộ link xem ảnh trả về 200 OK."],
          },
          {
            id: "fix-network-error-upload",
            title: "Sửa lỗi Network Error khi tải tệp lên từ trình duyệt",
            body: ["Trình duyệt không còn bị trỏ nhầm về localhost:9000 hay hostname nội bộ plane-minio."],
          },
        ],
      },
    ],
  },
  {
    id: "v1-4-1",
    version: "v1.4.1",
    title: "Slack Workspace Scope Guard, Real-time Changelog & Skill .Civix | Aug 19, 2026",
    formattedDate: "August 19, 2026",
    shortDate: "19 Aug, 2026",
    category: "Cloud",
    badgeText: "Bảo Mật & Tính Năng",
    summary:
      "Khắc phục triệt để lỗi định tuyến nhầm vào Workspace cá nhân khi sử dụng lệnh /agent từ Slack; ra mắt cổng tra cứu Documentation & Changelog chuyên biệt cùng bộ cẩm nang quy chuẩn làm việc Skill .Civix.",
    heroBannerTitle: "Slack Workspace Scope Guard, Real-time Changelog & Skill .Civix | Aug 19, 2026",
    sections: [
      {
        id: "whats-new",
        heading: "What's new",
        items: [
          {
            id: "slack-scope-guard",
            title: "Bảo Mật Định Tuyến Slack Workspace (Strict Scope Guard)",
            body: [
              "Ràng buộc bắt buộc Workspace được chọn phải có cấu hình SlackAutomation đang active và user gọi lệnh phải là thành viên hợp lệ (WorkspaceMember / ProjectMember).",
              "Xóa bỏ hoàn toàn cơ chế Fallback mù quáng về User #1 trong ContextResolver để triệt tiêu nguy cơ lộ dữ liệu cá nhân.",
            ],
            callout: {
              type: "warning",
              text: "Ngăn chặn tuyệt đối việc AI Bot đọc nhầm task từ workspace cá nhân sang kênh chat chung của công ty.",
            },
          },
          {
            id: "slack-changelog-agent",
            title: "Tích hợp Tra Cứu Changelog trực tiếp qua Slack",
            body: [
              "Thành viên có thể gõ câu hỏi tự nhiên trên Slack để nhận tóm tắt phiên bản và danh sách bug đã fix ngay lập tức.",
            ],
            code: "/agent có cập nhật gì mới không?\n/agent xem các bug đã fix ở phiên bản mới nhất\n/agent tóm tắt các tính năng của bản v1.4.1",
          },
        ],
      },
      {
        id: "enhancements",
        heading: "Enhancements",
        items: [
          {
            id: "mime-detection",
            title: "Trình Xem Trước Tệp Đính Kèm & Nhận Diện MIME Type",
            body: [
              "Bổ sung cơ chế fallback MIME type cho các định dạng văn bản (md, txt, json, csv, docx) giúp xem trước trực tiếp trên trình duyệt.",
            ],
          },
          {
            id: "skill-civix",
            title: "Bộ cẩm nang quy chuẩn làm việc Skill .Civix",
            body: [
              "Định nghĩa chuẩn viết tài liệu 5 phần, chuẩn viết release notes SemVer, quy ước Git commit và nguyên tắc vận hành an toàn cho AI Agent.",
            ],
          },
        ],
      },
      {
        id: "bug-fixes",
        heading: "Bug fixes",
        items: [
          {
            id: "fix-context-resolver",
            title: "Sửa lỗi ContextResolver chọn nhầm Workspace",
            body: [
              "Yêu cầu xác thực danh tính người dùng và kiểm tra quyền thành viên trước khi trả về dữ liệu dự án.",
            ],
          },
        ],
      },
    ],
  },
  {
    id: "v1-4-0",
    version: "v1.4.0",
    title: "Trello Board Importer, AIMarkdownRenderer & AI Gateway | Aug 17, 2026",
    formattedDate: "August 17, 2026",
    shortDate: "17 Aug, 2026",
    category: "Cloud",
    summary:
      "Tích hợp công cụ nhập dữ liệu từ Trello Board, trình render Markdown tối ưu hóa cho AI không phụ thuộc thư viện ngoài, hỗ trợ AI Gateway tùy biến và hệ thống sao lưu tự động 5 phút.",
    heroBannerTitle: "Trello Board Importer, AIMarkdownRenderer & AI Gateway | Aug 17, 2026",
    sections: [
      {
        id: "whats-new",
        heading: "What's new",
        items: [
          {
            id: "trello-importer",
            title: "Bộ nhập dữ liệu Trello Board JSON (Trello Importer)",
            body: [
              "Cho phép tải lên tệp JSON xuất từ Trello, tự động chuyển đổi danh sách thành trạng thái (States), thẻ (Labels), mô tả và phân công thành viên trong Plane.",
            ],
          },
          {
            id: "ai-markdown",
            title: "Trình hiển thị AIMarkdownRenderer độc quyền",
            body: [
              "Thiết kế zero-dependency tương thích hoàn hảo với production bundler, hỗ trợ nút sao chép code 1 chạm, bảng biểu dữ liệu và giao diện Dark/Light mượt mà.",
            ],
          },
          {
            id: "ai-gateway",
            title: "Civix Custom AI Gateway Provider",
            body: [
              "Hỗ trợ kết nối các mô hình ngôn ngữ lớn qua Custom Base URL, tự động xử lý User-Agent để tránh bị tường lửa Cloudflare/WAF chặn kết nối.",
            ],
          },
        ],
      },
      {
        id: "enhancements",
        heading: "Enhancements",
        items: [
          {
            id: "backup-suite",
            title: "Bộ sao lưu dữ liệu tự động định kỳ 5 phút",
            body: [
              "Tự động xuất bản sao lưu PostgreSQL an toàn vào thư mục lưu trữ, hỗ trợ script phục hồi dữ liệu tương tác không cần nhập mật khẩu thủ công.",
            ],
          },
        ],
      },
    ],
  },
  {
    id: "v1-3-5",
    version: "v1.3.5",
    title: "Slack Socket Mode, Fast-Path Engine & HITL Approval | Aug 12, 2026",
    formattedDate: "August 12, 2026",
    shortDate: "12 Aug, 2026",
    category: "Self-hosted",
    summary:
      "Kết nối Slack Bot thời gian thực qua Socket Mode an toàn trong mạng nội bộ, thiết kế Block Kit tương tác cao và cơ chế kiểm soát Human-In-The-Loop.",
    heroBannerTitle: "Slack Socket Mode, Fast-Path Engine & HITL Approval | Aug 12, 2026",
    sections: [
      {
        id: "whats-new",
        heading: "What's new",
        items: [
          {
            id: "slack-socket-mode",
            title: "Hỗ trợ kết nối Socket Mode cho Slack Bot",
            body: [
              "Chạy bot trực tiếp trong mạng doanh nghiệp với Bot Token & App Token (xapp-), loại bỏ hoàn toàn sự phụ thuộc vào Ngrok hay Public Webhook IP.",
            ],
          },
          {
            id: "hitl-approval",
            title: "Cơ chế phê duyệt Human-In-The-Loop (HITL)",
            body: [
              "Khi Agent đề xuất tái phân bổ task trễ hạn (Workload Rebalance), hệ thống sẽ gửi nút xác nhận trước khi thực hiện thay đổi dữ liệu.",
            ],
          },
        ],
      },
      {
        id: "enhancements",
        heading: "Enhancements",
        items: [
          {
            id: "fast-path-engine",
            title: "Fast-Path Engine phản hồi siêu tốc (<50ms)",
            body: [
              "Tự động nhận diện ý định và truy vấn trực tiếp cơ sở dữ liệu cho các lệnh xem tiến độ, danh sách task mà không cần chờ LLM xử lý.",
            ],
          },
        ],
      },
    ],
  },
  {
    id: "v1-3-0",
    version: "v1.3.0",
    title: "Telegram Bot Tương Tác 2 Chiều, Tự Hủy Tin Nhắn & Đa Dự Án | Aug 05, 2026",
    formattedDate: "August 05, 2026",
    shortDate: "05 Aug, 2026",
    category: "Mobile",
    summary:
      "Nâng cấp toàn diện Telegram Bot hỗ trợ đàm thoại 2 chiều, tạo task tự động bằng AI, tự xóa tin nhắn sau 45s và quản lý nhiều dự án trong cùng một nhóm.",
    heroBannerTitle: "Telegram Bot Tương Tác 2 Chiều, Tự Hủy Tin Nhắn & Đa Dự Án | Aug 05, 2026",
    sections: [
      {
        id: "whats-new",
        heading: "What's new",
        items: [
          {
            id: "telegram-2way",
            title: "Tạo task và hỏi đáp thông minh qua Telegram Bot",
            body: [
              "Thành viên có thể gửi tin nhắn tự nhiên vào nhóm Telegram để Bot tự động tạo công việc và gán nhãn chính xác.",
            ],
          },
          {
            id: "telegram-self-destruct",
            title: "Tự động dọn dẹp tin nhắn phản hồi (Self-Destruct 45s)",
            body: [
              "Tin nhắn kết quả của Bot sẽ tự động biến mất sau 45 giây để giữ cho luồng thảo luận của nhóm chat luôn gọn gàng.",
            ],
          },
        ],
      },
    ],
  },
];
