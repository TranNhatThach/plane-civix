# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import logging

# Third party imports
from celery import shared_task

# Django imports
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.loader import render_to_string

# Module imports
from plane.db.models import User, Workspace, WorkspaceMemberInvite
from plane.license.utils.instance_value import get_email_configuration
from plane.utils.email import generate_plain_text_from_html
from plane.utils.exception_logger import log_exception


@shared_task
def workspace_invitation(email, workspace_id, token, current_site, inviter):
    try:
        user = User.objects.get(email=inviter)

        workspace = Workspace.objects.get(pk=workspace_id)
        workspace_member_invite = WorkspaceMemberInvite.objects.get(token=token, email=email)

        # Relative link
        relative_link = (
            f"/workspace-invitations/?invitation_id={workspace_member_invite.id}&slug={workspace.slug}&token={token}"  # noqa: E501
        )

        # The complete url including the domain
        abs_url = str(current_site) + relative_link

        (
            EMAIL_HOST,
            EMAIL_HOST_USER,
            EMAIL_HOST_PASSWORD,
            EMAIL_PORT,
            EMAIL_USE_TLS,
            EMAIL_USE_SSL,
            EMAIL_FROM,
        ) = get_email_configuration()

        # Subject of the email
        inviter_name = user.first_name or user.display_name or user.email
        subject = f"{inviter_name} đã mời bạn tham gia không gian làm việc {workspace.name} trên Civix"

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
                            <span style="font-size: 12px; color: #94a3b8;">Lời Mời Tham Gia</span>
                        </td>
                    </tr>
                </table>
            </div>

            <!-- Main Body -->
            <div style="padding: 28px;">
                <p style="font-size: 15px; color: #334155; margin: 0 0 14px 0;">Xin chào,</p>
                <p style="font-size: 14px; line-height: 1.6; color: #475569; margin: 0 0 20px 0;">
                    <strong>{inviter_name}</strong> đã gửi lời mời bạn tham gia cộng tác trong không gian làm việc <strong>{workspace.name}</strong> trên nền tảng quản trị công việc <strong>Civix</strong>.
                </p>

                <!-- Workspace Metadata Table -->
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width: 100%; border-collapse: collapse; margin-bottom: 24px; background: #ffffff; border: 1px solid #f1f5f9; border-radius: 8px;">
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px; width: 140px;">Workspace:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-size: 14px; font-weight: 600;">{workspace.name}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Mã định danh (Slug):</td>
                        <td style="padding: 10px 14px; color: #475569; font-size: 13px; font-family: monospace;">{workspace.slug}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Người gửi lời mời:</td>
                        <td style="padding: 10px 14px; color: #0f172a; font-size: 13px; font-weight: 500;">{inviter_name} ({user.email})</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 14px; color: #64748b; font-size: 13px;">Email người nhận:</td>
                        <td style="padding: 10px 14px; color: #2563eb; font-size: 13px; font-weight: 500;">{email}</td>
                    </tr>
                </table>

                <!-- Primary Call To Action -->
                <div style="text-align: center; margin: 28px 0;">
                    <a href="{abs_url}" style="background-color: #0f172a; color: #ffffff; padding: 13px 36px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; display: inline-block; letter-spacing: 0.3px;">
                        Tham Gia Không Gian Làm Việc &rarr;
                    </a>
                </div>

                <!-- Quick start steps -->
                <div style="background: #f8fafc; border-radius: 6px; padding: 14px 18px; margin: 24px 0 0 0;">
                    <div style="font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 8px;">Hướng dẫn kích hoạt:</div>
                    <ol style="margin: 0; padding-left: 18px; font-size: 13px; color: #64748b; line-height: 1.6;">
                        <li>Nhấp vào nút <strong>Tham Gia Không Gian Làm Việc</strong> ở trên hoặc liên kết bên dưới.</li>
                        <li>Đăng nhập hoặc đăng ký tài khoản bằng chính địa chỉ email <strong style="color: #0f172a;">{email}</strong>.</li>
                        <li>Sau khi xác thực, hệ thống sẽ tự động đưa bạn vào Workspace và gán quyền tương ứng.</li>
                    </ol>
                </div>

                <div style="margin-top: 20px; font-size: 12px; color: #64748b; line-height: 1.5;">
                    Nếu nút trên không hoạt động, bạn có thể sao chép và dán liên kết sau vào trình duyệt:<br>
                    <a href="{abs_url}" style="color: #2563eb; text-decoration: none; word-break: break-all;">{abs_url}</a>
                </div>

                <!-- Footer -->
                <div style="margin-top: 32px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; line-height: 1.6;">
                    <p style="margin: 0 0 4px 0;">Thư mời này được tạo riêng cho địa chỉ {email}. Nếu bạn không yêu cầu, vui lòng bỏ qua email này.</p>
                    <p style="margin: 0;">&copy; Civix Platform. Nền tảng quản trị dự án & công việc doanh nghiệp.</p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

        text_content = generate_plain_text_from_html(html_content)

        workspace_member_invite.message = text_content
        workspace_member_invite.save()

        connection = get_connection(
            host=EMAIL_HOST,
            port=int(EMAIL_PORT),
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
            "Workspace invitation email sent successfully to %s for workspace %s", email, workspace.slug
        )
        return
    except (Workspace.DoesNotExist, WorkspaceMemberInvite.DoesNotExist):
        return
    except Exception as e:
        log_exception(e)
        return
