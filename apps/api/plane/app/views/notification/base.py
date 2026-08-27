# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Django imports
from django.db.models import Exists, OuterRef, Q, Case, When, BooleanField
from django.utils import timezone

# Third party imports
from rest_framework import status
from rest_framework.response import Response

from plane.app.serializers import (
    NotificationSerializer,
    UserNotificationPreferenceSerializer,
)
from plane.db.models import (
    Issue,
    IssueAssignee,
    IssueSubscriber,
    Notification,
    UserNotificationPreference,
    WorkspaceMember,
)
from plane.utils.paginator import BasePaginator
from plane.utils.order_queryset import NOTIFICATION_ORDER_BY_ALLOWLIST, sanitize_order_by
from plane.app.permissions import allow_permission, ROLE

# Module imports
from ..base import BaseAPIView, BaseViewSet


class NotificationViewSet(BaseViewSet, BasePaginator):
    model = Notification
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                workspace__slug=self.kwargs.get("slug"),
                receiver_id=self.request.user.id,
            )
            .select_related("workspace", "project", "triggered_by", "receiver")
        )

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def list(self, request, slug):
        # Get query parameters
        snoozed = request.GET.get("snoozed", "false")
        archived = request.GET.get("archived", "false")
        read = request.GET.get("read", None)
        type = request.GET.get("type", "all")
        mentioned = request.GET.get("mentioned", False)
        q_filters = Q()

        intake_issue = Issue.objects.filter(
            pk=OuterRef("entity_identifier"),
            issue_intake__status__in=[0, 2, -2],
            workspace__slug=self.kwargs.get("slug"),
        )

        notifications = (
            Notification.objects.filter(workspace__slug=slug, receiver_id=request.user.id)
            .filter(entity_name="issue")
            .annotate(is_inbox_issue=Exists(intake_issue))
            .annotate(is_intake_issue=Exists(intake_issue))
            .annotate(
                is_mentioned_notification=Case(
                    When(sender__icontains="mentioned", then=True),
                    default=False,
                    output_field=BooleanField(),
                )
            )
            .select_related("workspace", "project", "triggered_by", "receiver")
            .order_by("snoozed_till", "-created_at")
        )

        # Filters based on query parameters
        snoozed_filters = {
            "true": Q(snoozed_till__lt=timezone.now()) | Q(snoozed_till__isnull=False),
            "false": Q(snoozed_till__gte=timezone.now()) | Q(snoozed_till__isnull=True),
        }

        notifications = notifications.filter(snoozed_filters[snoozed])

        archived_filters = {
            "true": Q(archived_at__isnull=False),
            "false": Q(archived_at__isnull=True),
        }

        notifications = notifications.filter(archived_filters[archived])

        if read == "false":
            notifications = notifications.filter(read_at__isnull=True)

        if read == "true":
            notifications = notifications.filter(read_at__isnull=False)

        if mentioned:
            notifications = notifications.filter(sender__icontains="mentioned")
        else:
            notifications = notifications.exclude(sender__icontains="mentioned")

        type = type.split(",")
        # Subscribed issues
        if "subscribed" in type:
            issue_ids = (
                IssueSubscriber.objects.filter(workspace__slug=slug, subscriber_id=request.user.id)
                .annotate(created=Exists(Issue.objects.filter(created_by=request.user, pk=OuterRef("issue_id"))))
                .annotate(assigned=Exists(IssueAssignee.objects.filter(pk=OuterRef("issue_id"), assignee=request.user)))
                .filter(created=False, assigned=False)
                .values_list("issue_id", flat=True)
            )
            q_filters |= Q(entity_identifier__in=issue_ids)

        # Assigned Issues
        if "assigned" in type:
            issue_ids = IssueAssignee.objects.filter(workspace__slug=slug, assignee_id=request.user.id).values_list(
                "issue_id", flat=True
            )
            q_filters |= Q(entity_identifier__in=issue_ids)

        # Created issues
        if "created" in type:
            if WorkspaceMember.objects.filter(
                workspace__slug=slug, member=request.user, role__lt=15, is_active=True
            ).exists():
                notifications = notifications.none()
            else:
                issue_ids = Issue.objects.filter(workspace__slug=slug, created_by=request.user).values_list(
                    "pk", flat=True
                )
                q_filters |= Q(entity_identifier__in=issue_ids)

        # Apply the combined Q object filters
        notifications = notifications.filter(q_filters)

        # Pagination
        if request.GET.get("per_page", False) and request.GET.get("cursor", False):
            return self.paginate(
                order_by=sanitize_order_by(
                    request.GET.get("order_by", "-created_at"),
                    NOTIFICATION_ORDER_BY_ALLOWLIST,
                    "-created_at",
                ),
                request=request,
                queryset=(notifications),
                on_results=lambda notifications: NotificationSerializer(notifications, many=True).data,
            )

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def partial_update(self, request, slug, pk):
        notification = Notification.objects.get(workspace__slug=slug, pk=pk, receiver=request.user)
        # Only read_at and snoozed_till can be updated
        notification_data = {"snoozed_till": request.data.get("snoozed_till", None)}
        serializer = NotificationSerializer(notification, data=notification_data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def mark_read(self, request, slug, pk):
        notification = Notification.objects.get(receiver=request.user, workspace__slug=slug, pk=pk)
        notification.read_at = timezone.now()
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def mark_unread(self, request, slug, pk):
        notification = Notification.objects.get(receiver=request.user, workspace__slug=slug, pk=pk)
        notification.read_at = None
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def archive(self, request, slug, pk):
        notification = Notification.objects.get(receiver=request.user, workspace__slug=slug, pk=pk)
        notification.archived_at = timezone.now()
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def unarchive(self, request, slug, pk):
        notification = Notification.objects.get(receiver=request.user, workspace__slug=slug, pk=pk)
        notification.archived_at = None
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UnreadNotificationEndpoint(BaseAPIView):
    use_read_replica = True

    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def get(self, request, slug):
        # Watching Issues Count
        unread_notifications_count = (
            Notification.objects.filter(
                workspace__slug=slug,
                receiver_id=request.user.id,
                read_at__isnull=True,
                archived_at__isnull=True,
                snoozed_till__isnull=True,
            )
            .exclude(sender__icontains="mentioned")
            .count()
        )

        mention_notifications_count = Notification.objects.filter(
            workspace__slug=slug,
            receiver_id=request.user.id,
            read_at__isnull=True,
            archived_at__isnull=True,
            snoozed_till__isnull=True,
            sender__icontains="mentioned",
        ).count()

        return Response(
            {
                "total_unread_notifications_count": int(unread_notifications_count),
                "mention_unread_notifications_count": int(mention_notifications_count),
            },
            status=status.HTTP_200_OK,
        )


class MarkAllReadNotificationViewSet(BaseViewSet):
    @allow_permission(allowed_roles=[ROLE.ADMIN, ROLE.MEMBER, ROLE.GUEST], level="WORKSPACE")
    def create(self, request, slug):
        snoozed = request.data.get("snoozed", False)
        archived = request.data.get("archived", False)
        type = request.data.get("type", "all")

        notifications = (
            Notification.objects.filter(workspace__slug=slug, receiver_id=request.user.id, read_at__isnull=True)
            .select_related("workspace", "project", "triggered_by", "receiver")
            .order_by("snoozed_till", "-created_at")
        )

        # Filter for snoozed notifications
        if snoozed:
            notifications = notifications.filter(Q(snoozed_till__lt=timezone.now()) | Q(snoozed_till__isnull=False))
        else:
            notifications = notifications.filter(Q(snoozed_till__gte=timezone.now()) | Q(snoozed_till__isnull=True))

        # Filter for archived or unarchive
        if archived:
            notifications = notifications.filter(archived_at__isnull=False)
        else:
            notifications = notifications.filter(archived_at__isnull=True)

        # Subscribed issues
        if type == "watching":
            issue_ids = IssueSubscriber.objects.filter(workspace__slug=slug, subscriber_id=request.user.id).values_list(
                "issue_id", flat=True
            )
            notifications = notifications.filter(entity_identifier__in=issue_ids)

        # Assigned Issues
        if type == "assigned":
            issue_ids = IssueAssignee.objects.filter(workspace__slug=slug, assignee_id=request.user.id).values_list(
                "issue_id", flat=True
            )
            notifications = notifications.filter(entity_identifier__in=issue_ids)

        # Created issues
        if type == "created":
            if WorkspaceMember.objects.filter(
                workspace__slug=slug, member=request.user, role__lt=15, is_active=True
            ).exists():
                notifications = Notification.objects.none()
            else:
                issue_ids = Issue.objects.filter(workspace__slug=slug, created_by=request.user).values_list(
                    "pk", flat=True
                )
                notifications = notifications.filter(entity_identifier__in=issue_ids)

        updated_notifications = []
        for notification in notifications:
            notification.read_at = timezone.now()
            updated_notifications.append(notification)
        Notification.objects.bulk_update(updated_notifications, ["read_at"], batch_size=100)
        return Response({"message": "Successful"}, status=status.HTTP_200_OK)


class UserNotificationPreferenceEndpoint(BaseAPIView):
    model = UserNotificationPreference
    serializer_class = UserNotificationPreferenceSerializer

    # request the object
    def get(self, request):
        user_notification_preference, _ = UserNotificationPreference.objects.get_or_create(user=request.user)
        serializer = UserNotificationPreferenceSerializer(user_notification_preference)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # update the object
    def patch(self, request):
        user_notification_preference, _ = UserNotificationPreference.objects.get_or_create(user=request.user)
        serializer = UserNotificationPreferenceSerializer(user_notification_preference, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserNotificationTestEmailEndpoint(BaseAPIView):
    """Endpoint to dispatch a test notification email directly to user or custom email address."""

    def post(self, request):
        user = request.user
        custom_email = (request.data.get("email") or "").strip()
        recipient_email = custom_email if custom_email else (user.email if user and user.email else "")

        if not recipient_email:
            return Response(
                {"error": "Vui lòng nhập địa chỉ email hợp lệ để nhận thử nghiệm."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.core.mail import EmailMultiAlternatives, get_connection
        from django.utils.html import strip_tags
        from plane.license.utils.instance_value import get_email_configuration

        (
            EMAIL_HOST,
            EMAIL_HOST_USER,
            EMAIL_HOST_PASSWORD,
            EMAIL_PORT,
            EMAIL_USE_TLS,
            EMAIL_USE_SSL,
            EMAIL_FROM,
        ) = get_email_configuration()

        if not EMAIL_HOST or not EMAIL_FROM:
            return Response(
                {"error": "Máy chủ SMTP chưa được cấu hình (EMAIL_HOST hoặc EMAIL_FROM còn trống)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            connection = get_connection(
                host=EMAIL_HOST,
                port=int(EMAIL_PORT) if EMAIL_PORT else 587,
                username=EMAIL_HOST_USER,
                password=EMAIL_HOST_PASSWORD,
                use_tls=str(EMAIL_USE_TLS) == "1",
                use_ssl=str(EMAIL_USE_SSL) == "1",
                timeout=20,
            )

            user_name = user.display_name or user.first_name or user.email.split("@")[0]
            current_time_str = timezone.now().strftime("%H:%M:%S, ngày %d/%m/%Y")

            subject = f"[Civix Test] Kiểm tra thông báo qua Email - {user_name}"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #e2e8f0; margin: 0; padding: 24px; }}
                .card {{ max-width: 580px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3); }}
                .header {{ background: linear-gradient(135deg, #3b82f6, #6366f1); padding: 28px 24px; text-align: center; color: #ffffff; }}
                .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }}
                .content {{ padding: 24px; }}
                .info-box {{ background: #0f172a; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 14px 18px; margin: 18px 0; }}
                .info-row {{ margin: 6px 0; font-size: 13px; color: #94a3b8; }}
                .info-row strong {{ color: #f1f5f9; }}
                .badge {{ display: inline-block; background: #3b82f6/20; color: #60a5fa; border: 1px solid #3b82f6/40; border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 600; }}
                .footer {{ border-top: 1px solid #334155; padding: 16px 24px; font-size: 12px; color: #64748b; text-align: center; }}
              </style>
            </head>
            <body>
              <div class="card">
                <div class="header">
                  <h1>🚀 Kiểm tra kết nối Email thành công!</h1>
                  <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 13px;">Civix Notification System • Test Dispatch</p>
                </div>
                <div class="content">
                  <p style="font-size: 15px; margin-top: 0;">Xin chào <strong>{user_name}</strong>,</p>
                  <p style="font-size: 13px; line-height: 1.6; color: #cbd5e1;">
                    Đây là email thử nghiệm được gửi từ hệ thống quản lý công việc <strong>Civix (Plane)</strong>. Việc nhận được email này xác nhận kênh thông báo qua hộp thư cá nhân của bạn đã được kết nối và hoạt động hoàn hảo.
                  </p>
                  <div class="info-box">
                    <div class="info-row"><strong>Hộp thư người nhận:</strong> {recipient_email}</div>
                    <div class="info-row"><strong>Thời điểm phát lệnh:</strong> {current_time_str}</div>
                    <div class="info-row"><strong>Trạng thái máy chủ SMTP:</strong> <span style="color: #4ade80; font-weight: 600;">Đã sẵn sàng (Connected)</span></div>
                  </div>
                  <p style="font-size: 13px; line-height: 1.6; color: #94a3b8;">
                    Bạn sẽ nhận được email tự động khi có các sự kiện như: <em>Được nhắc tên trực tiếp (@mention)</em>, <em>Giao việc mới (Assigned)</em>, hoặc <em>Cập nhật trạng thái công việc</em> dựa trên tùy chỉnh cá nhân tại mục Cài đặt thông báo.
                  </p>
                </div>
                <div class="footer">
                  Civix Project Management Platform • Bản quyền © 2026 Civix
                </div>
              </div>
            </body>
            </html>
            """
            text_content = strip_tags(html_content)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=EMAIL_FROM,
                to=[recipient_email],
                connection=connection,
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            return Response(
                {
                    "message": f"Email thử nghiệm đã được gửi thành công đến {recipient_email}!",
                    "email": recipient_email,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Không thể gửi email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

