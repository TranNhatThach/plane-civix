/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState, useEffect } from "react";
import useSWR from "swr";
import { MessageSquare, Send, ShieldCheck } from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { Input } from "@plane/ui";
import { SlackIntegrationService, type ISlackAutomationData } from "@/services/integrations/slack.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
  initialData?: ISlackAutomationData;
  onSuccess?: () => void;
};

const slackService = new SlackIntegrationService();

export function SlackIntegrationForm({ workspaceSlug, projectId, initialData, onSuccess }: Props) {
  const { data: automations, mutate } = useSWR(
    workspaceSlug ? `SLACK_AUTOMATION_${workspaceSlug}_${projectId}` : null,
    () => slackService.getSlackAutomations(workspaceSlug, projectId),
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    }
  );

  const existingConfig = automations && automations.length > 0 ? automations[0] : initialData;

  const [webhookUrl, setWebhookUrl] = useState(existingConfig?.webhook_url || "");
  const [channelName, setChannelName] = useState(existingConfig?.channel_name || "");
  const [isActive, setIsActive] = useState(existingConfig?.is_active ?? true);
  const [botToken, setBotToken] = useState(existingConfig?.bot_token || "");
  const [appToken, setAppToken] = useState(existingConfig?.app_token || "");
  const [events, setEvents] = useState({
    issue_created: existingConfig?.events?.issue_created ?? true,
    issue_updated: existingConfig?.events?.issue_updated ?? true,
    comment_created: existingConfig?.events?.comment_created ?? true,
  });

  const [restrictCommands, setRestrictCommands] = useState(existingConfig?.events?.restrict_commands ?? false);
  const [allowedUsers, setAllowedUsers] = useState(
    (existingConfig?.events?.allowed_users || existingConfig?.events?.allowed_creators || []).join(", ")
  );

  useEffect(() => {
    if (automations && automations.length > 0) {
      const config = automations[0];
      if (config.webhook_url) setWebhookUrl(config.webhook_url);
      if (config.channel_name) setChannelName(config.channel_name);
      setIsActive(config.is_active ?? true);
      if (config.bot_token) setBotToken(config.bot_token);
      if (config.app_token) setAppToken(config.app_token);
      if (config.events) {
        setEvents({
          issue_created: config.events.issue_created ?? true,
          issue_updated: config.events.issue_updated ?? true,
          comment_created: config.events.comment_created ?? true,
        });
        setRestrictCommands(config.events.restrict_commands ?? false);
        setAllowedUsers((config.events.allowed_users || config.events.allowed_creators || []).join(", "));
      }
    }
  }, [automations]);

  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const handleTestConnection = async (e?: React.MouseEvent) => {
    if (e) e.preventDefault();
    if (!webhookUrl) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Validation Error",
        message: "Please enter your Slack Webhook URL before testing.",
      });
      return;
    }

    setIsTesting(true);
    try {
      const res = await slackService.sendTestMessage(workspaceSlug, projectId, {
        webhook_url: webhookUrl,
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Test Message Sent!",
        message: res.message || "Test Block Kit message sent to Slack channel successfully.",
      });
    } catch (err: any) {
      const errorMsg =
        typeof err === "string"
          ? err
          : err?.error || err?.message || JSON.stringify(err) || "Could not send test message.";
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Test Failed",
        message: errorMsg,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!webhookUrl) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Validation Error",
        message: "Slack Webhook URL is required.",
      });
      return;
    }

    setIsSaving(true);
    try {
      const parsedUsers = allowedUsers
        .split(",")
        .map((s: string) => s.trim())
        .filter(Boolean);

      await slackService.createOrUpdateSlackAutomation(workspaceSlug, projectId, {
        webhook_url: webhookUrl,
        channel_name: channelName,
        is_active: isActive,
        bot_token: botToken,
        app_token: appToken,
        events: {
          ...events,
          restrict_commands: restrictCommands,
          allowed_users: parsedUsers,
        },
      });

      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Slack Configuration Saved",
        message: "Slack Webhook notifications and permission controls configured successfully.",
      });

      mutate();
      if (onSuccess) onSuccess();
    } catch (err: any) {
      const errorMsg =
        typeof err === "string"
          ? err
          : err?.error || err?.message || JSON.stringify(err) || "Failed to save Slack configuration.";
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error Saving",
        message: errorMsg,
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="border-border-subtle bg-bg-surface-2 shadow-sm my-4 w-full space-y-5 rounded-lg border p-5">
      {/* Header */}
      <div className="border-border-subtle flex items-center justify-between border-b pb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-emerald-500/10 text-emerald-500 flex h-10 w-10 items-center justify-center rounded-lg">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-16 font-semibold text-primary">Slack Webhook & AI Agent Integration</h3>
            <p className="text-13 text-secondary">
              Automatically publish issue updates to your Slack channel and configure Socket Mode AI Agent.
            </p>
          </div>
        </div>
        <label htmlFor="slack-active-toggle" className="flex cursor-pointer items-center space-x-2">
          <span className="text-13 font-medium text-secondary">Active</span>
          <input
            id="slack-active-toggle"
            name="slack-active-toggle"
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 h-4 w-4 cursor-pointer rounded"
          />
        </label>
      </div>

      <form onSubmit={handleSave} className="space-y-5">
        {/* Webhook Configuration */}
        <div className="space-y-4">
          <div>
            <label htmlFor="slack-webhook-url" className="mb-1 block text-13 font-medium text-tertiary">
              Slack Incoming Webhook URL <span className="text-red-500">*</span>
            </label>
            <Input
              id="slack-webhook-url"
              name="slack-webhook-url"
              type="url"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
              className="w-full"
              required
            />
            <p className="mt-1 text-12 text-tertiary">
              Create an Incoming Webhook in your Slack App configuration and paste the URL here.
            </p>
          </div>

          <div>
            <label htmlFor="slack-channel-name" className="mb-1 block text-13 font-medium text-tertiary">
              Channel Name / Target (Optional)
            </label>
            <Input
              id="slack-channel-name"
              name="slack-channel-name"
              type="text"
              value={channelName}
              onChange={(e) => setChannelName(e.target.value)}
              placeholder="#proj-civix-updates"
              className="w-full"
            />
          </div>

          {/* Trigger Events */}
          <div className="space-y-2 pt-2">
            <span className="block text-13 font-medium text-tertiary">Trigger Events</span>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <label className="flex cursor-pointer items-center space-x-2 text-13 text-secondary">
                <input
                  type="checkbox"
                  checked={events.issue_created}
                  onChange={(e) => setEvents({ ...events, issue_created: e.target.checked })}
                  className="border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 h-4 w-4 rounded"
                />
                <span>📌 New Task Created</span>
              </label>
              <label className="flex cursor-pointer items-center space-x-2 text-13 text-secondary">
                <input
                  type="checkbox"
                  checked={events.issue_updated}
                  onChange={(e) => setEvents({ ...events, issue_updated: e.target.checked })}
                  className="border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 h-4 w-4 rounded"
                />
                <span>🔄 Status Changed</span>
              </label>
              <label className="flex cursor-pointer items-center space-x-2 text-13 text-secondary">
                <input
                  type="checkbox"
                  checked={events.comment_created}
                  onChange={(e) => setEvents({ ...events, comment_created: e.target.checked })}
                  className="border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 h-4 w-4 rounded"
                />
                <span>💬 New Comment Added</span>
              </label>
            </div>
          </div>
        </div>

        {/* Socket Mode Tokens */}
        <div className="border-border-subtle space-y-4 border-t pt-4">
          <div className="flex items-center space-x-3">
            <div className="bg-purple-500/10 text-purple-500 flex h-10 w-10 items-center justify-center rounded-lg">
              🤖
            </div>
            <div>
              <h4 className="text-14 font-semibold text-primary">Slack AI Agent — Socket Mode</h4>
              <p className="text-12 text-tertiary">
                Cấu hình Bot Token & App Token để kích hoạt lệnh <code>/agent</code> trên Slack mà không cần ngrok.
              </p>
            </div>
          </div>

          <div>
            <label htmlFor="slack-bot-token" className="mb-1 block text-13 font-medium text-tertiary">
              Bot User OAuth Token (xoxb-...)
            </label>
            <Input
              id="slack-bot-token"
              name="slack-bot-token"
              type="password"
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              placeholder="xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full"
            />
            <p className="mt-1 text-12 text-tertiary">
              Lấy từ trang Slack API → <strong>OAuth & Permissions</strong> → Bot User OAuth Token.
            </p>
          </div>

          <div>
            <label htmlFor="slack-app-token" className="mb-1 block text-13 font-medium text-tertiary">
              App-Level Token (xapp-...)
            </label>
            <Input
              id="slack-app-token"
              name="slack-app-token"
              type="password"
              value={appToken}
              onChange={(e) => setAppToken(e.target.value)}
              placeholder="xapp-x-xxxxxxxxxxxxxxx-xxxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full"
            />
            <p className="mt-1 text-12 text-tertiary">
              Lấy từ trang Slack API → <strong>Basic Information</strong> → App-Level Tokens → Generate Token (scope:{" "}
              <code>connections:write</code>).
            </p>
          </div>
        </div>

        {/* Permission Controls Section */}
        <div className="border-border-subtle space-y-3 border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="text-custom-primary-500 h-5 w-5" />
              <div>
                <h4 className="text-13 font-medium text-primary">Phân quyền thực thi lệnh (/agent)</h4>
                <p className="text-12 text-tertiary">
                  Giới hạn chỉ những người có Slack User ID hoặc @username được phép sử dụng AI Agent.
                </p>
              </div>
            </div>
            <label className="flex cursor-pointer items-center gap-2 text-13 font-medium text-secondary">
              <input
                type="checkbox"
                checked={restrictCommands}
                onChange={(e) => setRestrictCommands(e.target.checked)}
                className="border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 h-4 w-4 cursor-pointer rounded"
              />
              <span>Bật giới hạn quyền</span>
            </label>
          </div>

          {restrictCommands && (
            <div className="flex flex-col gap-1.5 pt-2">
              <label htmlFor="slack-allowed-users" className="text-13 font-medium text-tertiary">
                Danh sách Slack User IDs / Usernames được phép
              </label>
              <Input
                id="slack-allowed-users"
                name="slack-allowed-users"
                type="text"
                value={allowedUsers}
                onChange={(e) => setAllowedUsers(e.target.value)}
                placeholder="U0123456789, @nam, @admin"
                className="w-full"
              />
              <p className="text-11 text-tertiary">
                💡 Người dùng có thể gõ lệnh <code className="font-mono font-semibold text-primary">/agent myid</code>{" "}
                trên Slack để lấy nhanh User ID của họ. Điền các ID/Username phân cách bằng dấu phẩy.
              </p>
            </div>
          )}
        </div>

        {/* Examples */}
        <div className="border-border-subtle bg-bg-surface-1 space-y-1 rounded border p-3 text-12">
          <span className="block text-13 font-semibold text-primary">💬 Ví dụ sử dụng lệnh /agent:</span>
          <p className="text-secondary">
            • <code className="font-mono text-primary">/agent myid</code> — Xem Slack User ID để gửi cho Quản trị viên
            phân quyền.
          </p>
          <p className="text-secondary">
            • <code className="font-mono text-primary">/agent Báo cáo tiến độ Civix</code> — AI tự động phân tích & xuất
            % progress bar.
          </p>
          <p className="text-secondary">
            • <code className="font-mono text-primary">/agent Danh sách task của Nam</code> — Tra cứu công việc đang gán
            cho Nam.
          </p>
          <p className="text-secondary">
            • <code className="font-mono text-primary">/agent Có những task nào quá hạn không?</code> — Tự động lọc các
            task trễ hạn.
          </p>
          <p className="text-secondary">
            • <code className="font-mono text-primary">/agent Tạo task fix bug API gán cho @Nam hạn thứ 6</code> — AI tự
            tạo task.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="border-border-subtle flex items-center justify-between border-t pt-4">
          <Button
            type="button"
            variant="secondary"
            onClick={handleTestConnection}
            loading={isTesting}
            className="flex items-center space-x-2"
          >
            <Send className="h-4 w-4" />
            <span>Test Webhook Connection</span>
          </Button>

          <Button type="submit" variant="primary" loading={isSaving}>
            {isSaving ? "Saving..." : "Save Slack Configuration"}
          </Button>
        </div>
      </form>
    </div>
  );
}
