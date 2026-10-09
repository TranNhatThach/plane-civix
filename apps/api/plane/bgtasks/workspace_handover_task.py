# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import os
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from plane.license.utils.instance_value import get_email_configuration
from plane.utils.exception_logger import log_exception


@shared_task
def send_workspace_handover_email(
    email: str,
    workspace_name: str,
    workspace_slug: str,
    admin_name: str = "",
    temp_password: str = None,
    base_url: str = None,
):
    """
    Sends workspace onboarding & credentials handover email to the customer workspace admin.
    """
    try:
        # Resolve clean frontend base_url, avoiding any Django API port (:8000) leakage
        default_web_url = (
            getattr(settings, "WEB_URL", None)
            or os.environ.get("WEB_URL")
            or getattr(settings, "APP_BASE_URL", None)
            or "http://localhost"
        ).rstrip("/")

        if not base_url or ":8000" in base_url:
            base_url = default_web_url
        else:
            base_url = base_url.rstrip("/")

        workspace_url = f"{base_url}/{workspace_slug}"

        (
            EMAIL_HOST,
            EMAIL_HOST_USER,
            EMAIL_HOST_PASSWORD,
            EMAIL_PORT,
            EMAIL_USE_TLS,
            EMAIL_USE_SSL,
            EMAIL_FROM,
        ) = get_email_configuration()

        display_name = admin_name or email.split("@")[0]
        subject = f"[Civix] Thông tin bàn giao Workspace: {workspace_name}"

        # Build text & html body
        if temp_password:
            credentials_section_text = (
                f"THÔNG TIN ĐĂNG NHẬP BAN ĐẦU:\n"
                f"- Email: {email}\n"
                f"- Mật khẩu tạm thời: {temp_password}\n"
                f"- Thời hạn: 7 ngày kể từ thời điểm khởi tạo\n\n"
                f"LƯU Ý BẢO MẬT: Mật khẩu trên là thông tin khởi tạo tạm thời. "
                f"Hệ thống yêu cầu đổi mật khẩu mới ngay trong lần truy cập đầu tiên."
            )
            credentials_section_html = f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin: 22px 0;">
                <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px;">Thông Tin Tài Khoản Quản Trị</div>
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 6px 0; color: #64748b; font-size: 13px; width: 140px;">Tài khoản (Email):</td>
                        <td style="padding: 6px 0; color: #0f172a; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">{email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #64748b; font-size: 13px; vertical-align: middle;">Mật khẩu tạm thời:</td>
                        <td style="padding: 6px 0;">
                            <span style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 15px; font-weight: 700; color: #0f172a; background-color: #e2e8f0; padding: 4px 10px; border-radius: 6px; letter-spacing: 1px; display: inline-block;">{temp_password}</span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 6px 0; color: #64748b; font-size: 13px;">Thời hạn hiệu lực:</td>
                        <td style="padding: 6px 0; color: #475569; font-size: 13px;">7 ngày kể từ khi tạo</td>
                    </tr>
                </table>
                <div style="margin-top: 14px; padding: 10px 14px; background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 3px solid #f59e0b; border-radius: 4px; font-size: 12px; line-height: 1.5; color: #92400e;">
                    <strong>Lưu ý bảo mật:</strong> Đây là mật khẩu khởi tạo tạm thời. Vì lý do an toàn dữ liệu, Quý khách được yêu cầu đổi mật khẩu mới ngay trong lần đăng nhập đầu tiên.
                </div>
            </div>
            """
        else:
            credentials_section_text = (
                f"Tài khoản của bạn ({email}) đã được cấp quyền Quản trị viên (Admin) cho Workspace này.\n"
                f"Quý khách có thể sử dụng mật khẩu hiện tại để đăng nhập trực tiếp."
            )
            credentials_section_html = f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin: 22px 0;">
                <div style="font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px;">Phân Quyền Quản Trị Viên</div>
                <p style="margin: 0 0 6px 0; font-size: 14px; color: #1e293b; line-height: 1.5;">
                    Tài khoản <strong>{email}</strong> đã được chỉ định làm Quản trị viên (Admin) cho Workspace <strong>{workspace_name}</strong>.
                </p>
                <p style="margin: 0; font-size: 13px; color: #64748b;">
                    Quý khách có thể sử dụng mật khẩu hiện tại của tài khoản để đăng nhập trực tiếp.
                </p>
            </div>
            """

        text_content = (
            f"Xin chào {display_name},\n\n"
            f"Workspace quản trị dự án {workspace_name} đã sẵn sàng trên hệ thống Civix Platform.\n\n"
            f"THÔNG TIN KHÔNG GIAN LÀM VIỆC:\n"
            f"- Workspace: {workspace_name}\n"
            f"- Mã định danh: {workspace_slug}\n"
            f"- Địa chỉ truy cập: {workspace_url}\n\n"
            f"{credentials_section_text}\n\n"
            f"Truy cập Workspace: {workspace_url}\n\n"
            f"Trân trọng,\n"
            f"Civix Platform Support"
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #1e293b; -webkit-font-smoothing: antialiased;">
    <div style="background-color: #f1f5f9; padding: 36px 16px;">
        <div style="max-width: 580px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            
            <!-- Header Bar -->
            <div style="background-color: #0f172a; padding: 22px 28px; border-bottom: 1px solid #1e293b;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                    <tr>
                        <td>
                            <span style="font-size: 18px; font-weight: 800; letter-spacing: -0.3px; color: #ffffff;">CIVIX</span>
                            <span style="display: inline-block; margin-left: 8px; padding: 2px 8px; background: rgba(255,255,255,0.1); border-radius: 4px; font-size: 11px; font-weight: 500; color: #94a3b8; vertical-align: middle;">WORKSPACES</span>
                        </td>
                        <td style="text-align: right;">
                            <span style="font-size: 12px; color: #94a3b8;">Bàn Giao Dự Án</span>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Main Body -->
            <div style="padding: 28px;">
                <p style="font-size: 15px; color: #334155; margin: 0 0 14px 0;">Xin chào <strong>{display_name}</strong>,</p>
                <p style="font-size: 14px; line-height: 1.6; color: #475569; margin: 0 0 20px 0;">
                    Không gian làm việc <strong>{workspace_name}</strong> của bạn đã được khởi tạo và sẵn sàng trên nền tảng Civix. Dưới đây là thông tin quản trị và đường dẫn truy cập trực tiếp.
                </p>

                <!-- Workspace Metadata Table -->
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width: 100%; border-collapse: collapse; margin-bottom: 20px; background: #ffffff; border: 1px solid #f1f5f9; border-radius: 8px;">
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px; width: 140px;">Workspace:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-size: 14px; font-weight: 600;">{workspace_name}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Mã định danh (Slug):</td>
                        <td style="padding: 10px 14px; color: #475569; font-size: 13px; font-family: monospace;">{workspace_slug}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Địa chỉ truy cập:</td>
                        <td style="padding: 10px 14px; font-size: 13px;">
                            <a href="{workspace_url}" style="color: #2563eb; text-decoration: none; word-break: break-all;">{workspace_url}</a>
                        </td>
                    </tr>
                </table>

                {credentials_section_html}

                <!-- Primary Call To Action -->
                <div style="text-align: center; margin: 28px 0;">
                    <a href="{workspace_url}" style="background-color: #0f172a; color: #ffffff; padding: 13px 36px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; display: inline-block; letter-spacing: 0.3px;">
                        Truy Cập Workspace &rarr;
                    </a>
                </div>

                <!-- Quick start steps -->
                <div style="background: #f8fafc; border-radius: 6px; padding: 14px 18px; margin: 24px 0 0 0;">
                    <div style="font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 8px;">Các bước kích hoạt nhanh:</div>
                    <ol style="margin: 0; padding-left: 18px; font-size: 13px; color: #64748b; line-height: 1.6;">
                        <li>Nhấp vào nút <strong>Truy Cập Workspace</strong> hoặc liên kết trực tiếp ở trên.</li>
                        <li>Đăng nhập bằng thông tin tài khoản được cấp.</li>
                        <li>Cập nhật mật khẩu chính thức theo hướng dẫn bảo mật để bắt đầu làm việc.</li>
                    </ol>
                </div>

                <!-- Footer -->
                <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; line-height: 1.6;">
                    <p style="margin: 0 0 4px 0;">Email này được gửi tự động từ Civix Platform theo yêu cầu khởi tạo tài nguyên.</p>
                    <p style="margin: 0;">Vui lòng không chia sẻ thông tin đăng nhập trong email này cho người khác. &copy; Civix Platform.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

        connection = get_connection(
            host=EMAIL_HOST,
            port=int(EMAIL_PORT) if EMAIL_PORT else 587,
            username=EMAIL_HOST_USER,
            password=EMAIL_HOST_PASSWORD,
            use_tls=EMAIL_USE_TLS == "1",
            use_ssl=EMAIL_USE_SSL == "1",
        )

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=EMAIL_FROM,
            to=[email],
            connection=connection,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logging.getLogger("plane.worker").info(
            "Workspace handover email sent successfully to %s for workspace %s (url: %s)",
            email,
            workspace_slug,
            workspace_url,
        )
        return True
    except Exception as e:
        log_exception(e)
        logging.getLogger("plane.worker").error("Failed to send workspace handover email: %s", str(e))
        return False
