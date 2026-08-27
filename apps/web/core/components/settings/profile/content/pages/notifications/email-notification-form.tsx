/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState, useEffect } from "react";
import { observer } from "mobx-react";
import { Controller, useForm } from "react-hook-form";
import {
  AtSign,
  UserPlus,
  MessageSquare,
  GitBranch,
  CheckCircle2,
  Sliders,
  Calendar,
  Mail,
  ShieldCheck,
  Zap,
  Activity,
  Send,
  Inbox,
} from "lucide-react";
// plane imports
import { useTranslation } from "@plane/i18n";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { Button } from "@plane/propel/button";
import type { IUserEmailNotificationSettings } from "@plane/types";
import { ToggleSwitch } from "@plane/ui";
import { useUser } from "@/hooks/store/user";
// services
import { UserService } from "@/services/user.service";

type Props = {
  data: IUserEmailNotificationSettings;
};

const DEFAULT_EMAIL_NOTIFICATION_SETTINGS: IUserEmailNotificationSettings = {
  property_change: true,
  state_change: true,
  comment: true,
  mention: true,
  issue_completed: true,
  email_assigned: true,
  email_due_date: true,
  email_digest: false,
  email_instant_mention: true,
  email_instant_assigned: true,
  notify_self_actions: false,
};

const userService = new UserService();

export const NotificationsProfileSettingsForm = observer(function NotificationsProfileSettingsForm(props: Props) {
  const { data } = props;
  const { t } = useTranslation();
  const { data: currentUser } = useUser();

  const [isSendingTestEmail, setIsSendingTestEmail] = useState(false);
  const [customEmail, setCustomEmail] = useState("");
  const [testEmailSentTo, setTestEmailSentTo] = useState<string | null>(null);

  const { control, reset } = useForm<IUserEmailNotificationSettings>({
    defaultValues: {
      ...DEFAULT_EMAIL_NOTIFICATION_SETTINGS,
      ...data,
    },
  });

  const handleSendTestEmail = async () => {
    setIsSendingTestEmail(true);
    try {
      const targetInput = customEmail.trim() || undefined;
      const res = await userService.sendTestEmailNotification(targetInput);
      const targetEmail = res?.email || targetInput || currentUser?.email || "hộp thư của bạn";
      setTestEmailSentTo(targetEmail);
      setToast({
        title: "Đã gửi email thử nghiệm!",
        type: TOAST_TYPE.SUCCESS,
        message: `Email kiểm tra đã được gửi thành công đến ${targetEmail}. Hãy mở hộp thư để kiểm tra!`,
      });
    } catch (error: any) {
      const errMsg =
        error?.error ||
        error?.message ||
        "Không thể gửi email thử nghiệm. Vui lòng kiểm tra lại địa chỉ email hoặc cấu hình SMTP của máy chủ.";
      setToast({
        title: "Gửi email thất bại",
        type: TOAST_TYPE.ERROR,
        message: errMsg,
      });
    } finally {
      setIsSendingTestEmail(false);
    }
  };

  const handleSettingChange = async (key: keyof IUserEmailNotificationSettings, value: boolean) => {
    try {
      await userService.updateCurrentUserEmailNotificationSettings({
        [key]: value,
      });
      setToast({
        title: t("success"),
        type: TOAST_TYPE.SUCCESS,
        message: t("email_notification_setting_updated_successfully"),
      });
    } catch (_error) {
      setToast({
        title: t("error"),
        type: TOAST_TYPE.ERROR,
        message: t("failed_to_update_email_notification_setting"),
      });
    }
  };

  useEffect(() => {
    reset({
      ...DEFAULT_EMAIL_NOTIFICATION_SETTINGS,
      ...data,
    });
  }, [reset, data]);

  const recipientEmail = currentUser?.email || "Chưa xác định email";

  return (
    <div className="flex max-w-3xl flex-col gap-y-8">
      {/* Test Email Dispatch Card */}
      <div className="border-custom-primary-100/30 bg-custom-primary-100/[0.04] shadow-xs relative overflow-hidden rounded-2xl border p-5 transition-all">
        <div className="flex items-start gap-3.5">
          <div className="bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border">
            <Mail className="h-5 w-5" />
          </div>
          <div className="w-full">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm text-custom-text-100 font-bold">Kiểm tra kết nối Email (Test Email Delivery)</h3>
              <span className="border-custom-border-200 bg-custom-background-90 text-custom-text-200 inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[11px] font-medium">
                <Inbox className="text-emerald-500 h-3 w-3" />
                Email tài khoản: {recipientEmail}
              </span>
            </div>
            <p className="text-xs text-custom-text-300 mt-1 leading-relaxed">
              Bạn có thể nhập một địa chỉ email bất kỳ bên dưới để kiểm tra khả năng nhận email thông báo thực tế từ hệ
              thống Civix qua máy chủ SMTP.
            </p>

            {/* Input & Action Button Row */}
            <div className="mt-3.5 flex flex-col gap-2.5 sm:flex-row sm:items-center">
              <div className="relative flex-1">
                <input
                  type="email"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  placeholder={`Nhập email nhận test (mặc định: ${recipientEmail})`}
                  className="bg-custom-background-90/90 border-custom-border-200 text-custom-text-100 placeholder:text-custom-text-400 focus:border-custom-primary-100 focus:bg-custom-background-100 focus:ring-custom-primary-100/30 text-xs w-full rounded-xl border px-3.5 py-2 transition-all focus:ring-1 focus:outline-none"
                />
              </div>
              <Button
                type="button"
                variant="primary"
                size="sm"
                loading={isSendingTestEmail}
                onClick={handleSendTestEmail}
                className="shadow-sm inline-flex shrink-0 items-center gap-1.5"
              >
                {!isSendingTestEmail && <Send className="h-3.5 w-3.5" />}
                <span>{isSendingTestEmail ? "Đang gửi email..." : "Gửi email thử nghiệm"}</span>
              </Button>
            </div>
          </div>
        </div>

        {testEmailSentTo && (
          <div className="border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs mt-3.5 flex items-center gap-2 rounded-xl border px-3.5 py-2 font-medium">
            <CheckCircle2 className="text-emerald-500 h-4 w-4 shrink-0" />
            <span>
              Đã gửi email thử nghiệm thành công đến <strong>{testEmailSentTo}</strong>! Vui lòng kiểm tra hộp thư đến
              (hoặc hòm thư rác/Spam).
            </span>
          </div>
        )}
      </div>
      {/* Group 1: Instant Alerts */}
      <section className="space-y-4">
        <div className="border-border-200/60 flex items-center justify-between border-b pb-3">
          <div className="flex items-center gap-2.5">
            <div className="bg-blue-500/10 text-blue-500 rounded-lg p-1.5">
              <Zap className="size-4" />
            </div>
            <div>
              <h3 className="text-sm text-text-100 font-semibold tracking-tight">
                Thông báo thời gian thực (Instant Alerts)
              </h3>
              <p className="text-xs text-text-400 mt-0.5">
                Gửi email tức thì ngay khi có sự kiện trực tiếp cần bạn phản hồi
              </p>
            </div>
          </div>
          <span className="bg-blue-500/10 text-blue-500 border-blue-500/20 rounded border px-2 py-0.5 text-[11px] font-medium">
            Realtime
          </span>
        </div>

        <div className="grid gap-2">
          {/* Mention */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <AtSign className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Nhắc tên trực tiếp (@Mention)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Nhận email ngay lập tức khi bạn được nhắc tên trong bình luận hoặc phần mô tả công việc.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="email_instant_mention"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value ?? true}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("email_instant_mention", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>

          {/* Assigned */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <UserPlus className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Được giao việc mới (Assigned)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Nhận email thông báo ngay khi được phân công làm người phụ trách task mới.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="email_instant_assigned"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value ?? true}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("email_instant_assigned", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>
        </div>
      </section>

      {/* Group 2: Activity Updates */}
      <section className="space-y-4">
        <div className="border-border-200/60 flex items-center gap-2.5 border-b pb-3">
          <div className="bg-surface-200 text-text-200 rounded-lg p-1.5">
            <Activity className="size-4" />
          </div>
          <div>
            <h3 className="text-sm text-text-100 font-semibold tracking-tight">
              Cập nhật tiến độ & Thảo luận (Activity Updates)
            </h3>
            <p className="text-xs text-text-400 mt-0.5">
              Tùy chỉnh thông báo cho các công việc bạn đã tạo hoặc đang theo dõi
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          {/* Comments */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <MessageSquare className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Bình luận mới (Comments)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Thông báo khi có phản hồi hoặc thảo luận mới trên công việc bạn đang theo dõi.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="comment"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("comment", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>

          {/* State change */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <GitBranch className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Thay đổi trạng thái tiến độ (State Change)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Thông báo khi trạng thái chuyển đổi (Todo, In Progress, In Review, Done).
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="state_change"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("state_change", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>

          {/* Completed */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <CheckCircle2 className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Công việc hoàn thành (Issue Completed)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Chỉ nhận thông báo khi công việc chính thức được đánh dấu hoàn thành.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="issue_completed"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("issue_completed", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>

          {/* Properties */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <Sliders className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Thuộc tính bổ trợ (Property Changes)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Thông báo khi mức độ ưu tiên, nhãn dán, Cycle hoặc Module thay đổi.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="property_change"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("property_change", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>
        </div>
      </section>

      {/* Group 3: Deadlines & Digest */}
      <section className="space-y-4">
        <div className="border-border-200/60 flex items-center gap-2.5 border-b pb-3">
          <div className="bg-surface-200 text-text-200 rounded-lg p-1.5">
            <Calendar className="size-4" />
          </div>
          <div>
            <h3 className="text-sm text-text-100 font-semibold tracking-tight">
              Thời hạn & Báo cáo (Deadlines & Digest)
            </h3>
            <p className="text-xs text-text-400 mt-0.5">Cảnh báo nhắc nhở tự động hạn chót và bản tin tổng hợp</p>
          </div>
        </div>

        <div className="grid gap-2">
          {/* Due date */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <Calendar className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Cảnh báo hạn chót (Due Date & Overdue)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Nhận email nhắc nhở trước 24 giờ khi sắp đến hạn chót hoặc khi công việc bị quá hạn.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="email_due_date"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value ?? true}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("email_due_date", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>

          {/* Digest */}
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <Mail className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">Bản tin công việc đầu ngày (Daily Digest)</div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Gửi 1 email tóm tắt vào 08:00 sáng mỗi ngày liệt kê danh sách việc cần giải quyết trong ngày.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="email_digest"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value ?? false}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("email_digest", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>
        </div>
      </section>

      {/* Group 4: Anti-Spam */}
      <section className="space-y-4">
        <div className="border-border-200/60 flex items-center gap-2.5 border-b pb-3">
          <div className="bg-surface-200 text-text-200 rounded-lg p-1.5">
            <ShieldCheck className="size-4" />
          </div>
          <div>
            <h3 className="text-sm text-text-100 font-semibold tracking-tight">
              Quy tắc chống trùng lặp (Anti-Spam Filter)
            </h3>
            <p className="text-xs text-text-400 mt-0.5">
              Kiểm soát việc nhận email cho các thao tác của chính bản thân
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          <div className="border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 flex items-start justify-between rounded-xl border p-3.5 transition-colors">
            <div className="flex items-start gap-3">
              <div className="bg-surface-200 text-text-300 mt-0.5 rounded-md p-1.5">
                <ShieldCheck className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs text-text-100 font-semibold">
                  Nhận email cho hành động do chính mình thực hiện
                </div>
                <div className="text-xs text-text-400 max-w-lg leading-relaxed">
                  Mặc định tắt để giữ hộp thư sạch sẽ. Bật tùy chọn này nếu bạn muốn nhận bản sao lưu email cho các thao
                  tác do chính bạn thực hiện.
                </div>
              </div>
            </div>
            <Controller
              control={control}
              name="notify_self_actions"
              render={({ field: { value, onChange } }) => (
                <ToggleSwitch
                  value={value ?? false}
                  onChange={(newValue) => {
                    onChange(newValue);
                    handleSettingChange("notify_self_actions", newValue);
                  }}
                  size="sm"
                />
              )}
            />
          </div>
        </div>
      </section>
    </div>
  );
});
