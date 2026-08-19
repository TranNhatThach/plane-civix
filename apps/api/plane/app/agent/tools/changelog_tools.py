import logging
from typing import Optional, Dict, Any, List
from plane.app.agent.registry import agent_tool
from plane.app.agent.core.scope_guard import scope_guard

logger = logging.getLogger(__name__)

# Structured Civix Version Changelogs
CIVIX_CHANGELOGS = [
    {
        "version": "v1.4.1",
        "title": "Bảo Mật Định Tuyến Slack Workspace & Hệ Thống Changelog / Skill .Civix",
        "release_date": "19/08/2026",
        "is_latest": True,
        "summary": "Khắc phục triệt để lỗi định tuyến nhầm vào Workspace cá nhân khi sử dụng lệnh /agent từ Slack; ra mắt cổng tra cứu Documentation & Changelog chuyên biệt cùng bộ cẩm nang Skill .Civix.",
        "highlights": [
            "Khắc phục lỗi Agent bốc nhầm Workspace cá nhân khi sếp gõ lệnh trên Slack",
            "Xóa bỏ cơ chế Fallback mù quáng về User #1 trong ContextResolver",
            "Tự động map danh tính Slack User với Plane User qua Email an toàn",
            "Ra mắt trang Changelog Timeline chuyên biệt (/changelog)",
            "Tích hợp tra cứu phiên bản & bug fixes trực tiếp qua lệnh /agent trên Slack",
            "Ban hành bộ cẩm nang văn hóa công sở và quy chuẩn kỹ thuật Skill .Civix",
        ],
        "fixes": [
            "Sửa lỗi Slack Agent gọi nhầm Workspace cá nhân thay vì Workspace công ty",
            "Sửa lỗi fallback mù quáng sang User đầu tiên trong DB",
        ],
        "features": [
            "Cổng Documentation & Changelog chuyên biệt cho Civix (/changelog)",
            "Bộ cẩm nang quy chuẩn làm việc và văn hóa công sở Skill .Civix",
        ],
        "agent_updates": [
            "Tích hợp tool tra cứu Changelog vào Slack AI Agent",
            "Socket Mode Handler bắt lỗi phân quyền và gửi tin nhắn hướng dẫn kèm Slack User ID",
        ]
    },
    {
        "version": "v1.4.0",
        "title": "Trello Board Importer, AIMarkdownRenderer & AI Gateway Provider",
        "release_date": "17/08/2026",
        "is_latest": False,
        "summary": "Tích hợp công cụ nhập dữ liệu từ Trello Board, trình render Markdown tối ưu hóa cho AI không phụ thuộc thư viện ngoài, hỗ trợ AI Gateway tùy biến và hệ thống sao lưu tự động 5 phút.",
        "highlights": [
            "Công cụ Trello Board Importer nhập dữ liệu kèm ánh xạ tự động trạng thái & nhãn",
            "AIMarkdownRenderer độc quyền hỗ trợ copy code block, bảng biểu và typography",
            "Hỗ trợ Civix Custom AI Gateway Provider (DeepSeek, Gemini, OpenRouter)",
            "Bộ công cụ sao lưu dữ liệu tự động mỗi 5 phút (5-min automated backup suite)",
        ],
        "fixes": [
            "Sửa lỗi WAF/Cloudflare chặn User-Agent khi gọi Custom AI Gateway",
            "Sửa lỗi nhắc mật khẩu trong lệnh restore PostgreSQL định kỳ",
        ],
        "features": [
            "Bộ nhập dữ liệu Trello Board JSON (Trello Importer)",
            "Trình hiển thị AIMarkdownRenderer độc quyền zero-dependency",
            "Hệ thống sao lưu tự động PostgreSQL 5 phút",
        ],
        "agent_updates": [
            "Civix Custom AI Gateway Provider kết nối DeepSeek & Gemini",
            "Bảng điều khiển AI Agent & Harness controls trong Admin UI",
        ]
    },
    {
        "version": "v1.3.5",
        "title": "Slack Socket Mode, Fast-Path Engine & Phê Duyệt An Toàn HITL",
        "release_date": "12/08/2026",
        "is_latest": False,
        "summary": "Kết nối Slack Bot thời gian thực qua Socket Mode an toàn trong mạng nội bộ, thiết kế Block Kit tương tác cao và cơ chế kiểm soát Human-In-The-Loop.",
        "highlights": [
            "Kết nối Slack Socket Mode thời gian thực không cần mở port Public IP",
            "Giao diện thẻ Block Kit 2 cột trực quan với visual progress bar",
            "Fast-Path Pattern Matcher phản hồi truy vấn dưới 50ms",
            "Cơ chế Human-In-The-Loop: Nút [Xác nhận] / [Hủy] điều chuyển công việc",
        ],
        "fixes": [
            "Sửa lỗi tự động chọn dự án có task hoạt động và render tin nhắn rỗng",
        ],
        "features": [
            "Thẻ thông tin tương tác Slack Block Kit Card 2 cột",
            "Lệnh tra cứu nhanh /agent myid",
        ],
        "agent_updates": [
            "Hỗ trợ kết nối Socket Mode an toàn trong mạng nội bộ",
            "Fast-Path Engine xử lý siêu tốc (<50ms) cho các truy vấn xem tiến độ",
            "Cơ chế phê duyệt Human-In-The-Loop (HITL) cho tác vụ Workload Rebalance",
        ]
    },
    {
        "version": "v1.3.0",
        "title": "Telegram Bot Tương Tác 2 Chiều, Tự Hủy Tin Nhắn & Đa Dự Án",
        "release_date": "05/08/2026",
        "is_latest": False,
        "summary": "Nâng cấp toàn diện Telegram Bot hỗ trợ đàm thoại 2 chiều, tạo task tự động bằng AI, tự xóa tin nhắn sau 45s và quản lý nhiều dự án trong cùng một nhóm.",
        "highlights": [
            "Telegram Bot tương tác 2 chiều với chế độ AI Q&A",
            "Tính năng tự hủy tin nhắn (Self-destruct messages) sau 45s",
            "Hỗ trợ quản lý đa dự án linh hoạt trong cùng nhóm Telegram",
            "Form cấu hình TelegramIntegrationForm trong Workspace Settings",
        ],
        "fixes": [
            "Sửa lỗi trùng lặp tin nhắn Webhook trên Telegram khi mạng chập chờn",
        ],
        "features": [
            "Tạo task và hỏi đáp thông minh qua Telegram Bot",
            "Form cấu hình Telegram trong Workspace Settings",
        ],
        "agent_updates": [
            "Tự động xóa tin nhắn kết quả của Bot sau 45s chống loãng nhóm chat",
        ]
    },
    {
        "version": "v1.2.0",
        "title": "Nâng Cấp Kiến Trúc Django 5.2 LTS & React Router v7 Vite",
        "release_date": "20/07/2026",
        "is_latest": False,
        "summary": "Hiện đại hóa nền tảng kỹ thuật với Django 5.2 LTS (Python 3.13), React Router v7 trên nền Vite và mở rộng hỗ trợ nhiều nhà cung cấp AI tiên tiến.",
        "highlights": [
            "Nâng cấp Backend lên Django 5.2 LTS",
            "Chuyển đổi Frontend sang React Router v7 & Vite Build System",
            "Mở rộng hỗ trợ nhà cung cấp LLM (DeepSeek, Gemini 2.0, OpenAI)",
            "Quyền truy cập dự án công khai (Public Project Access) mượt mà",
        ],
        "fixes": [
            "Vá các cảnh báo bảo mật Dependabot và CodeQL",
        ],
        "features": [
            "Cho phép thành viên Workspace xem dự án công khai (Public Projects)",
        ],
        "agent_updates": [
            "Mở rộng hệ sinh thái mô hình AI DeepSeek, Gemini 2.0",
        ]
    }
]



@agent_tool(
    name="tool_get_changelog",
    description="Tra cứu nhật ký phiên bản (Changelog & Release Notes) của Civix, bao gồm các tính năng mới và các lỗi (bugs) đã được khắc phục.",
    parameters_schema={
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "Số phiên bản cụ thể cần tra cứu (ví dụ: 'v1.4.1', 'v1.4.0'). Bỏ trống để lấy phiên bản mới nhất.",
            },
            "only_fixes": {
                "type": "boolean",
                "description": "True nếu người dùng chỉ muốn xem danh sách các lỗi (bugs) đã được sửa.",
            }
        },
        "required": []
    }
)
@scope_guard(requires_project=False)
def tool_get_changelog(
    version: Optional[str] = None,
    only_fixes: bool = False,
    _context: Optional[Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Returns structured release notes and bug fixes for the requested version or latest release.
    """
    target_release = None
    if version:
        clean_v = version.strip().lower().lstrip("v")
        for rel in CIVIX_CHANGELOGS:
            if rel["version"].lower().lstrip("v") == clean_v:
                target_release = rel
                break

    if not target_release:
        # Default to latest version
        target_release = CIVIX_CHANGELOGS[0]

    return {
        "success": True,
        "version": target_release["version"],
        "title": target_release["title"],
        "release_date": target_release["release_date"],
        "is_latest": target_release.get("is_latest", False),
        "summary": target_release["summary"],
        "highlights": target_release.get("highlights", []),
        "fixes": target_release.get("fixes", []),
        "features": target_release.get("features", []),
        "agent_updates": target_release.get("agent_updates", []),
        "only_fixes": only_fixes,
        "all_versions": [r["version"] for r in CIVIX_CHANGELOGS],
    }
