/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export interface ITrelloImportResult {
  status: string;
  message: string;
  board_name: string;
  project_id: string;
  project_name: string;
  project_identifier: string;
  imported_tasks: number;
  created_states: number;
  created_labels: number;
}

export class TrelloIntegrationService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  async importTrello(
    workspaceSlug: string,
    projectId: string,
    params: {
      file?: File;
      data?: any;
      target_project_id?: string;
      create_new_project?: boolean;
      include_closed?: boolean;
    }
  ): Promise<ITrelloImportResult> {
    if (params.file) {
      const formData = new FormData();
      formData.append("file", params.file);
      if (params.target_project_id) {
        formData.append("target_project_id", params.target_project_id);
      }
      if (params.create_new_project !== undefined) {
        formData.append("create_new_project", String(params.create_new_project));
      }
      if (params.include_closed !== undefined) {
        formData.append("include_closed", String(params.include_closed));
      }

      return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/trello/import/`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      })
        .then((response) => response?.data)
        .catch((error) => {
          throw error?.response?.data || error;
        });
    }

    return this.post(`/api/workspaces/${workspaceSlug}/projects/${projectId}/trello/import/`, params)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data || error;
      });
  }
}
