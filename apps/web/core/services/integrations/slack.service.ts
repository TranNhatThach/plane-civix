/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export interface ISlackAutomationData {
  id?: string;
  webhook_url: string;
  channel_name?: string;
  is_active: boolean;
  events?: {
    issue_created?: boolean;
    issue_updated?: boolean;
    comment_created?: boolean;
  };
}

export class SlackIntegrationService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getSlackAutomations(workspaceSlug: string, projectId: string): Promise<ISlackAutomationData[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/projects/${projectId}/slack-automations/`)
      .then((response) => (Array.isArray(response?.data) ? response.data : []))
      .catch(() => []);
  }

  async createOrUpdateSlackAutomation(
    workspaceSlug: string,
    projectId: string,
    data: ISlackAutomationData
  ): Promise<ISlackAutomationData> {
    return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/slack-automations/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteSlackAutomation(workspaceSlug: string, projectId: string, automationId: string): Promise<void> {
    return this.delete(`/api/workspaces/${workspaceSlug}/projects/${projectId}/slack-automations/${automationId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async sendTestMessage(
    workspaceSlug: string,
    projectId: string,
    data: { webhook_url: string }
  ): Promise<{ success?: boolean; message?: string; error?: string }> {
    return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/slack-automations/test-message/`, data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}
