/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect } from "react";
import { observer } from "mobx-react";
import { Controller, useForm } from "react-hook-form";
// plane imports
import { useTranslation } from "@plane/i18n";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import type { IUserEmailNotificationSettings } from "@plane/types";
import { ToggleSwitch } from "@plane/ui";
// components
import { SettingsControlItem } from "@/components/settings/control-item";
// services
import { UserService } from "@/services/user.service";

type Props = {
  data: IUserEmailNotificationSettings;
};

// services
const userService = new UserService();

export const NotificationsProfileSettingsForm = observer(function NotificationsProfileSettingsForm(props: Props) {
  const { data } = props;
  // translation
  const { t } = useTranslation();
  // form data
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
    <div className="flex flex-col gap-y-6">
      {/* Group 1: Instant Alerts */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-subtle-1 pb-2">
          <span className="text-sm font-semibold text-text-100 flex items-center gap-1.5">
            ⚡ Thông Báo Tức Thì (Instant Realtime Alerts)
          </span>
          <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20">
            Ưu tiên cao
          </span>
        </div>
        <p className="text-xs text-text-400">
          Gửi email trực tiếp ngay lập tức khi có sự kiện cần sự chú ý hoặc phản hồi khẩn cấp của bạn.
        </p>

        <div className="flex flex-col gap-y-1">
          <SettingsControlItem
            title="Nhắc tên tôi (@Mention)"
            description="Gửi email ngay lập tức khi ai đó nhắc tên (@username) bạn trong bình luận hoặc mô tả task."
            control={
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
            }
          />
          <SettingsControlItem
            title="Được giao task mới (Assigned)"
            description="Gửi email ngay lập tức khi bạn được phân công làm người phụ trách một task mới."
            control={
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
            }
          />
        </div>
      </div>

      {/* Group 2: Activity & Updates */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-subtle-1 pb-2">
          <span className="text-sm font-semibold text-text-100 flex items-center gap-1.5">
            📦 Cập Nhật Tiến Độ & Bình Luận (Activity Updates)
          </span>
        </div>
        <p className="text-xs text-text-400">
          Tùy chỉnh nhận thông báo đối với các thay đổi trên task bạn đã tạo hoặc đang theo dõi (Subscribed).
        </p>

        <div className="flex flex-col gap-y-1">
          <SettingsControlItem
            title={t("comments")}
            description="Nhận thông báo khi có thảo luận hoặc bình luận mới trên các task bạn đang theo dõi."
            control={
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
            }
          />
          <SettingsControlItem
            title={t("state_change")}
            description="Nhận thông báo khi trạng thái tiến độ thay đổi (ví dụ: In Progress, In Review, Done)."
            control={
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
            }
          />
          <div className="border-l-3 border-subtle-1 pl-3">
            <SettingsControlItem
              title={t("issue_completed")}
              description="Chỉ thông báo khi task chính thức được đánh dấu Hoàn thành (Completed)."
              control={
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
              }
            />
          </div>
          <SettingsControlItem
            title={t("property_changes")}
            description="Nhận thông báo khi các thuộc tính phụ (Mức ưu tiên, Nhãn dán Labels, Sprint Cycle, Module) thay đổi."
            control={
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
            }
          />
        </div>
      </div>

      {/* Group 3: Deadlines & Digest */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-subtle-1 pb-2">
          <span className="text-sm font-semibold text-text-100 flex items-center gap-1.5">
            ⏰ Cảnh Báo Hạn Chót & Báo Cáo (Deadlines & Digest)
          </span>
        </div>
        <p className="text-xs text-text-400">
          Nhắc nhở tự động giúp bạn không bao giờ bỏ lỡ deadline công việc quan trọng.
        </p>

        <div className="flex flex-col gap-y-1">
          <SettingsControlItem
            title="Cảnh báo hạn chót (Due Date & Overdue)"
            description="Gửi email nhắc nhở trước 24 giờ khi task của bạn sắp đến hạn chót hoặc khi task đã quá hạn."
            control={
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
            }
          />
          <SettingsControlItem
            title="Bản tin tóm tắt công việc đầu ngày (Daily Morning Digest)"
            description="Nhận 1 email tổng hợp duy nhất vào 08:00 sáng mỗi ngày liệt kê danh sách việc cần làm trong ngày."
            control={
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
            }
          />
        </div>
      </div>

      {/* Group 4: Anti-Spam */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 border-b border-subtle-1 pb-2">
          <span className="text-sm font-semibold text-text-100 flex items-center gap-1.5">
            🛡️ Nguyên Tắc Chống Spam (Anti-Spam Filter)
          </span>
        </div>
        <p className="text-xs text-text-400">
          Tránh làm phiền hộp thư bởi chính các thao tác do bạn tự thực hiện.
        </p>

        <div className="flex flex-col gap-y-1">
          <SettingsControlItem
            title="Nhận email cho hành động do chính mình thực hiện"
            description="Khi bạn tự bình luận hoặc tự sửa task của mình, hệ thống sẽ mặc định KHÔNG gửi email cho chính bạn để tránh thư rác."
            control={
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
            }
          />
        </div>
      </div>
    </div>
  );
});
