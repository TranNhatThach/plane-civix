/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import type { IAppIntegration, IImporterService, IWorkspaceIntegration, IExportServiceResponse } from "@plane/types";
import { APIService } from "@/services/api.service";
// types
// helper

const DEFAULT_APP_INTEGRATIONS: IAppIntegration[] = [
  {
    id: "github-integration",
    title: "GitHub",
    provider: "github",
    network: 1,
    verified: true,
    author: "Plane",
    avatar_url: null,
    created_at: "",
    created_by: null,
    description: "Sync project work items with GitHub.",
    metadata: {},
    redirect_url: "",
    updated_at: "",
    updated_by: null,
    webhook_secret: "",
    webhook_url: "",
  },
  {
    id: "slack-integration",
    title: "Slack",
    provider: "slack",
    network: 1,
    verified: true,
    author: "Plane",
    avatar_url: null,
    created_at: "",
    created_by: null,
    description: "Sync project work items with Slack.",
    metadata: {},
    redirect_url: "",
    updated_at: "",
    updated_by: null,
    webhook_secret: "",
    webhook_url: "",
  },
];

export class IntegrationService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async getAppIntegrationsList(): Promise<IAppIntegration[]> {
    return this.get(`/api/integrations/`)
      .then((response) => (Array.isArray(response?.data) && response.data.length > 0 ? response.data : DEFAULT_APP_INTEGRATIONS))
      .catch(() => DEFAULT_APP_INTEGRATIONS);
  }

  async getWorkspaceIntegrationsList(workspaceSlug: string): Promise<IWorkspaceIntegration[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/workspace-integrations/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteWorkspaceIntegration(workspaceSlug: string, integrationId: string): Promise<any> {
    return this.delete(`/api/workspaces/${workspaceSlug}/workspace-integrations/${integrationId}/provider/`)
      .then((res) => res?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async getImporterServicesList(workspaceSlug: string): Promise<IImporterService[]> {
    return this.get(`/api/workspaces/${workspaceSlug}/importers/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
  async getExportsServicesList(
    workspaceSlug: string,
    cursor: string,
    per_page: number
  ): Promise<IExportServiceResponse> {
    return this.get(`/api/workspaces/${workspaceSlug}/export-issues`, {
      params: {
        per_page,
        cursor,
      },
    })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async deleteImporterService(workspaceSlug: string, service: string, importerId: string): Promise<any> {
    return this.delete(`/api/workspaces/${workspaceSlug}/importers/${service}/${importerId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}
