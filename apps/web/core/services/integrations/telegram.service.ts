/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export interface ITelegramAutomationData {
  id?: string;
  bot_token: string;
  chat_id: string;
  is_active: boolean;
  events?: {
    issue_created?: boolean;
    issue_updated?: boolean;
    comment_added?: boolean;
  };
}

export class TelegramIntegrationService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getTelegramAutomations(workspaceSlug: string, projectId: string): Promise<ITelegramAutomationData[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/telegram-automations/`)
      .then((response) => (Array.isArray(response?.data) ? response.data : []))
      .catch(() => []);
  }

  async createOrUpdateTelegramAutomation(
    workspaceSlug: string,
    projectId: string,
    data: ITelegramAutomationData
  ): Promise<ITelegramAutomationData> {
    return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/telegram-automations/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteTelegramAutomation(workspaceSlug: string, projectId: string, automationId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/projects/${projectId}/telegram-automations/${automationId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async sendTestMessage(
    workspaceSlug: string,
    projectId: string,
    data: { bot_token: string; chat_id: string }
  ): Promise<{ message?: string; error?: string }> {
    return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/telegram-automations/test-message/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}
