/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect } from "react";
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
} from "lucide-react";
// plane imports
import { useTranslation } from "@plane/i18n";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IUserEmailNotificationSettings } from "@plane/types";
import { ToggleSwitch } from "@plane/ui";
// services
import { UserService } from "@/services/user.service";

type Props = {
  data: IUserEmailNotificationSettings;
};

const userService = new UserService();

export const NotificationsProfileSettingsForm = observer(function NotificationsProfileSettingsForm(props: Props) {
  const { data } = props;
  const { t } = useTranslation();

  const { control, reset } = useForm<IUserEmailNotificationSettings>({
    defaultValues: {
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
      ...data,
    },
  });

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
      ...data,
    });
  }, [reset, data]);

  return (
    <div className="flex flex-col gap-y-8 max-w-3xl">
      {/* Group 1: Instant Alerts */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-border-200/60 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-500">
              <Zap className="size-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-text-100 tracking-tight">
                Thông báo thời gian thực (Instant Alerts)
              </h3>
              <p className="text-xs text-text-400 mt-0.5">
                Gửi email tức thì ngay khi có sự kiện trực tiếp cần bạn phản hồi
              </p>
            </div>
          </div>
          <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-blue-500/10 text-blue-500 border border-blue-500/20">
            Realtime
          </span>
        </div>

        <div className="grid gap-2">
          {/* Mention */}
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <AtSign className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Nhắc tên trực tiếp (@Mention)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <UserPlus className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Được giao việc mới (Assigned)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
        <div className="flex items-center gap-2.5 border-b border-border-200/60 pb-3">
          <div className="p-1.5 rounded-lg bg-surface-200 text-text-200">
            <Activity className="size-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-100 tracking-tight">
              Cập nhật tiến độ & Thảo luận (Activity Updates)
            </h3>
            <p className="text-xs text-text-400 mt-0.5">
              Tùy chỉnh thông báo cho các công việc bạn đã tạo hoặc đang theo dõi
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          {/* Comments */}
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <MessageSquare className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Bình luận mới (Comments)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <GitBranch className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Thay đổi trạng thái tiến độ (State Change)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <CheckCircle2 className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Công việc hoàn thành (Issue Completed)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <Sliders className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Thuộc tính bổ trợ (Property Changes)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
        <div className="flex items-center gap-2.5 border-b border-border-200/60 pb-3">
          <div className="p-1.5 rounded-lg bg-surface-200 text-text-200">
            <Calendar className="size-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-100 tracking-tight">
              Thời hạn & Báo cáo (Deadlines & Digest)
            </h3>
            <p className="text-xs text-text-400 mt-0.5">
              Cảnh báo nhắc nhở tự động hạn chót và bản tin tổng hợp
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          {/* Due date */}
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <Calendar className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Cảnh báo hạn chót (Due Date & Overdue)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <Mail className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Bản tin công việc đầu ngày (Daily Digest)
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
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
        <div className="flex items-center gap-2.5 border-b border-border-200/60 pb-3">
          <div className="p-1.5 rounded-lg bg-surface-200 text-text-200">
            <ShieldCheck className="size-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-100 tracking-tight">
              Quy tắc chống trùng lặp (Anti-Spam Filter)
            </h3>
            <p className="text-xs text-text-400 mt-0.5">
              Kiểm soát việc nhận email cho các thao tác của chính bản thân
            </p>
          </div>
        </div>

        <div className="grid gap-2">
          <div className="flex items-start justify-between p-3.5 rounded-xl border border-border-200/70 bg-surface-100/40 hover:bg-surface-100/80 transition-colors">
            <div className="flex items-start gap-3">
              <div className="p-1.5 rounded-md bg-surface-200 text-text-300 mt-0.5">
                <ShieldCheck className="size-3.5" />
              </div>
              <div className="space-y-0.5">
                <div className="text-xs font-semibold text-text-100">
                  Nhận email cho hành động do chính mình thực hiện
                </div>
                <div className="text-xs text-text-400 leading-relaxed max-w-lg">
                  Mặc định tắt để giữ hộp thư sạch sẽ. Bật tùy chọn này nếu bạn muốn nhận bản sao lưu email cho các thao tác do chính bạn thực hiện.
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
