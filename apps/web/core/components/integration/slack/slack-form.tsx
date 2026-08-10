/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState, useEffect } from "react";
import useSWR from "swr";
import { MessageSquare, Send } from "lucide-react";
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
      await slackService.createOrUpdateSlackAutomation(workspaceSlug, projectId, {
        webhook_url: webhookUrl,
        channel_name: channelName,
        is_active: isActive,
        bot_token: botToken,
        app_token: appToken,
        events,
      });

      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Slack Configuration Saved",
        message: "Slack Webhook notifications configured successfully.",
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
    <div className="w-full rounded-lg border border-border-subtle bg-bg-surface-2 p-5 shadow-sm space-y-5 my-4">
      <div className="flex items-center justify-between border-b border-border-subtle pb-4">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-16 font-semibold text-primary">Slack Webhook Notifications</h3>
            <p className="text-13 text-secondary">
              Automatically publish issue updates, new tasks, and comments to your Slack channel via Webhook.
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-13 font-medium text-secondary">Active</label>
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500 cursor-pointer"
          />
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label htmlFor="slack-webhook-url" className="text-13 font-medium text-tertiary block mb-1">
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
          <label htmlFor="slack-channel-name" className="text-13 font-medium text-tertiary block mb-1">
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

        <div className="space-y-2 pt-2">
          <label className="text-13 font-medium text-tertiary block">Trigger Events</label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <label className="flex items-center space-x-2 text-13 text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={events.issue_created}
                onChange={(e) => setEvents({ ...events, issue_created: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500"
              />
              <span>📌 New Task Created</span>
            </label>
            <label className="flex items-center space-x-2 text-13 text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={events.issue_updated}
                onChange={(e) => setEvents({ ...events, issue_updated: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500"
              />
              <span>🔄 Status Changed</span>
            </label>
            <label className="flex items-center space-x-2 text-13 text-secondary cursor-pointer">
              <input
                type="checkbox"
                checked={events.comment_created}
                onChange={(e) => setEvents({ ...events, comment_created: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300 text-custom-primary-600 focus:ring-custom-primary-500"
              />
              <span>💬 New Comment Added</span>
            </label>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-border-subtle">
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
            Save Slack Configuration
          </Button>
        </div>
      </form>

      <div className="pt-4 border-t border-border-subtle space-y-4">
        <div className="flex items-center space-x-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/10 text-purple-500">
            🤖
          </div>
          <div>
            <h4 className="text-14 font-semibold text-primary">Slack AI Agent — Socket Mode</h4>
            <p className="text-12 text-tertiary">
              Cấu hình Bot Token & App Token để kích hoạt lệnh <code>/agent</code> trên Slack.
              Không cần ngrok hay domain public.
            </p>
          </div>
        </div>

        <div>
          <label htmlFor="slack-bot-token" className="text-13 font-medium text-tertiary block mb-1">
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
          <label htmlFor="slack-app-token" className="text-13 font-medium text-tertiary block mb-1">
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
            Lấy từ trang Slack API → <strong>Basic Information</strong> → App-Level Tokens → Generate Token (scope: <code>connections:write</code>).
          </p>
        </div>

        <div className="rounded border border-border-subtle p-3 text-12 space-y-1 bg-bg-surface-1">
          <span className="font-semibold text-primary block text-13">💬 Ví dụ sử dụng lệnh /agent:</span>
          <p className="text-secondary">• <code className="text-primary font-mono">/agent Báo cáo tiến độ Civix</code> — AI tự động phân tích & xuất % progress bar.</p>
          <p className="text-secondary">• <code className="text-primary font-mono">/agent Danh sách task của Nam</code> — Tra cứu công việc đang gán cho Nam.</p>
          <p className="text-secondary">• <code className="text-primary font-mono">/agent Có những task nào quá hạn không?</code> — Tự động lọc các task trễ hạn.</p>
          <p className="text-secondary">• <code className="text-primary font-mono">/agent Tạo task fix bug API gán cho @Nam hạn thứ 6</code> — AI tự tạo task.</p>
        </div>
      </div>
    </div>
  );
}
