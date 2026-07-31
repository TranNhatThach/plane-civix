/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import { Send } from "lucide-react";
import { Button } from "@plane/propel/button";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
import { Input } from "@plane/ui";
import { TelegramIntegrationService, type ITelegramAutomationData } from "@/services/integrations/telegram.service";

type Props = {
  workspaceSlug: string;
  projectId: string;
  initialData?: ITelegramAutomationData;
  onSuccess?: () => void;
};

const telegramService = new TelegramIntegrationService();

export function TelegramIntegrationForm({ workspaceSlug, projectId, initialData, onSuccess }: Props) {
  const [botToken, setBotToken] = useState(initialData?.bot_token || "");
  const [chatId, setChatId] = useState(initialData?.chat_id || "");
  const [isActive, setIsActive] = useState(initialData?.is_active ?? true);
  const [events, setEvents] = useState({
    issue_created: initialData?.events?.issue_created ?? true,
    issue_updated: initialData?.events?.issue_updated ?? true,
    comment_added: initialData?.events?.comment_added ?? true,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const handleTestConnection = async () => {
    if (!botToken || !chatId) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Validation Error",
        message: "Please enter both Bot Token and Chat ID before testing.",
      });
      return;
    }

    setIsTesting(true);
    try {
      const res = await telegramService.sendTestMessage(workspaceSlug, projectId, {
        bot_token: botToken,
        chat_id: chatId,
      });
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Test Message Sent!",
        message: res.message || "Test message sent to Telegram group successfully.",
      });
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Test Failed",
        message: err?.error || "Could not send test message. Check your Bot Token and Chat ID.",
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!botToken || !chatId) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Validation Error",
        message: "Bot Token and Chat ID are required.",
      });
      return;
    }

    setIsSaving(true);
    try {
      await telegramService.createOrUpdateTelegramAutomation(workspaceSlug, projectId, {
        bot_token: botToken,
        chat_id: chatId,
        is_active: isActive,
        events,
      });

      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Saved!",
        message: "Telegram Bot notifications configured successfully.",
      });

      if (onSuccess) onSuccess();
    } catch (err: any) {
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error",
        message: err?.error || "Failed to save Telegram automation config.",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-6 rounded-lg border border-subtle bg-layer-1 p-6">
      <div className="flex items-center justify-between border-b border-subtle pb-4">
        <div>
          <h3 className="text-16 font-semibold text-primary">Telegram Bot Notifications</h3>
          <p className="text-13 text-tertiary">
            Receive real-time updates for issue creation, status changes, and comments in your Telegram group or chat.
          </p>
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-13 font-medium text-secondary">
          <span>Active</span>
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="h-4 w-4 rounded border-subtle text-accent-primary"
          />
        </label>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Bot Token Input */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="telegram-bot-token" className="text-13 font-medium text-tertiary">
            Bot Token
          </label>
          <Input
            id="telegram-bot-token"
            name="telegram-bot-token"
            type="password"
            value={botToken}
            onChange={(e) => setBotToken(e.target.value)}
            placeholder="7123456789:AAFxxxxxxxxxxxxxxxxx"
            className="w-full rounded-md"
          />
          <p className="text-11 text-tertiary">
            Obtain token by messaging <strong>@BotFather</strong> on Telegram and typing <code>/newbot</code>.
          </p>
        </div>

        {/* Chat ID Input */}
        <div className="flex flex-col gap-1.5">
          <label htmlFor="telegram-chat-id" className="text-13 font-medium text-tertiary">
            Chat ID
          </label>
          <Input
            id="telegram-chat-id"
            name="telegram-chat-id"
            type="text"
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
            placeholder="-5333292648"
            className="w-full rounded-md"
          />
          <p className="text-11 text-tertiary">
            Enter Group/Channel Chat ID (e.g. <code>-5333292648</code>). Add <strong>@getidsbot</strong> to your group
            to find it.
          </p>
        </div>
      </div>

      {/* Events Checkboxes */}
      <div className="space-y-3 pt-2">
        <h4 className="text-13 font-medium text-primary">Notification Triggers</h4>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <label className="flex cursor-pointer items-center gap-2 text-13 text-secondary">
            <input
              type="checkbox"
              checked={events.issue_created}
              onChange={(e) => setEvents({ ...events, issue_created: e.target.checked })}
              className="h-4 w-4 rounded border-subtle text-accent-primary"
            />
            <span>📌 Issue Created</span>
          </label>

          <label className="flex cursor-pointer items-center gap-2 text-13 text-secondary">
            <input
              type="checkbox"
              checked={events.issue_updated}
              onChange={(e) => setEvents({ ...events, issue_updated: e.target.checked })}
              className="h-4 w-4 rounded border-subtle text-accent-primary"
            />
            <span>🔄 Status Changed</span>
          </label>

          <label className="flex cursor-pointer items-center gap-2 text-13 text-secondary">
            <input
              type="checkbox"
              checked={events.comment_added}
              onChange={(e) => setEvents({ ...events, comment_added: e.target.checked })}
              className="h-4 w-4 rounded border-subtle text-accent-primary"
            />
            <span>💬 New Comment</span>
          </label>
        </div>
      </div>

      {/* Form Action Buttons */}
      <div className="flex items-center justify-between border-t border-subtle pt-4">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={handleTestConnection}
          loading={isTesting}
          className="flex items-center gap-1.5"
        >
          <Send className="size-4" />
          <span>Send Test Message</span>
        </Button>

        <Button type="submit" variant="primary" size="sm" loading={isSaving}>
          {isSaving ? "Saving..." : "Save Automation"}
        </Button>
      </div>
    </form>
  );
}
