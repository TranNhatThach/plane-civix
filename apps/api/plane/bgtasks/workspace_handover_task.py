# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

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
        if not base_url:
            base_url = getattr(settings, "WEB_URL", None) or "https://plane.civix.com.vn"
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
        subject = f"[Civix] Bàn giao Workspace quản trị dự án: {workspace_name}"

        # Build text & html body
        if temp_password:
            credentials_section_text = (
                f"Thông tin đăng nhập ban đầu:\n"
                f"- Email: {email}\n"
                f"- Mật khẩu tạm thời: {temp_password}\n"
                f"- Thời hạn mật khẩu tạm: 7 ngày\n\n"
                f"LƯU Ý BẢO MẬT: Để đảm bảo an toàn dữ liệu, Quý khách vui lòng đăng nhập và đổi mật khẩu mới ngay lần truy cập đầu tiên."
            )
            credentials_section_html = f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <p style="margin: 0 0 10px 0; font-weight: 600; color: #1e293b;">Thông tin đăng nhập ban đầu:</p>
                <p style="margin: 4px 0; color: #334155;"><strong>Email:</strong> <span style="font-family: monospace;">{email}</span></p>
                <p style="margin: 4px 0; color: #334155;"><strong>Mật khẩu tạm thời:</strong> <span style="font-family: monospace; background: #e0e7ff; padding: 2px 6px; border-radius: 4px; font-weight: bold; color: #3730a3;">{temp_password}</span></p>
                <p style="margin: 4px 0; color: #64748b; font-size: 13px;"><em>(Thời hạn mật khẩu tạm: 7 ngày)</em></p>
                <div style="margin-top: 12px; padding: 8px 12px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 4px; font-size: 13px; color: #92400e;">
                    <strong>Lưu ý bảo mật:</strong> Quý khách vui lòng đăng nhập và đổi mật khẩu mới ngay lần truy cập đầu tiên.
                </div>
            </div>
            """
        else:
            credentials_section_text = (
                f"Tài khoản của bạn ({email}) đã được kích hoạt quyền Quản trị (Admin) cho Workspace này.\n"
                f"Quý khách có thể sử dụng mật khẩu hiện tại để đăng nhập."
            )
            credentials_section_html = f"""
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <p style="margin: 0; color: #334155;">Tài khoản <strong>{email}</strong> đã được chỉ định làm Quản trị viên (Admin) của Workspace này.</p>
                <p style="margin: 8px 0 0 0; color: #64748b; font-size: 13px;">Quý khách có thể sử dụng mật khẩu hiện tại của tài khoản để đăng nhập trực tiếp.</p>
            </div>
            """

        text_content = (
            f"Kính gửi {display_name},\n\n"
            f"Hệ thống Civix xin trân trọng thông báo Workspace quản trị dự án của Quý khách đã được khởi tạo thành công.\n\n"
            f"Thông tin Workspace:\n"
            f"- Tên Workspace: {workspace_name}\n"
            f"- Đường dẫn truy cập: {workspace_url}\n\n"
            f"{credentials_section_text}\n\n"
            f"Truy cập ngay: {workspace_url}\n\n"
            f"Trân trọng,\n"
            f"Đội ngũ Vận hành Nền tảng Civix"
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{subject}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 24px;">
            <div style="text-align: center; margin-bottom: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 16px;">
                <h2 style="color: #0f172a; margin: 0;">CIVIX WORKSPACE PLATFORM</h2>
            </div>
            <p>Kính gửi <strong>{display_name}</strong>,</p>
            <p>Hệ thống Civix xin thông báo Workspace quản lý công việc và dự án của Quý khách đã được thiết lập thành công trên hệ thống <strong>{workspace_name}</strong>.</p>
            
            {credentials_section_html}

            <div style="text-align: center; margin: 32px 0;">
                <a href="{workspace_url}" style="background-color: #2563eb; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                    Truy Cập Workspace
                </a>
            </div>

            <p style="font-size: 13px; color: #64748b;">
                Nếu nút trên không hoạt động, Quý khách có thể sao chép và dán liên kết sau vào trình duyệt:<br>
                <a href="{workspace_url}" style="color: #2563eb;">{workspace_url}</a>
            </p>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 28px 0;">
            <p style="font-size: 12px; color: #94a3b8; text-align: center; margin: 0;">
                Email này được gửi tự động từ Hệ thống Quản trị Civix (plane.civix.com.vn). Vui lòng không trả lời trực tiếp email này.
            </p>
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
            "Workspace handover email sent successfully to %s for workspace %s", email, workspace_slug
        )
        return True
    except Exception as e:
        log_exception(e)
        logging.getLogger("plane.worker").error("Failed to send workspace handover email: %s", str(e))
        return False
