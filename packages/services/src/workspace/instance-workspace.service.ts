/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import type { IWorkspace, TWorkspacePaginationInfo } from "@plane/types";
import { APIService } from "../api.service";

/**
 * Service class for managing instance workspaces
 * Handles CRUD operations on instance workspaces
 * @extends APIService
 */
export class InstanceWorkspaceService extends APIService {
  /**
   * Constructor for InstanceWorkspaceService
   * @param BASE_URL - Base URL for API requests
   */
  constructor(BASE_URL?: string) {
    super(BASE_URL || API_BASE_URL);
  }

  /**
   * Retrieves a paginated list of workspaces for the current instance
   * @param {string} nextPageCursor - Optional cursor to retrieve the next page of results
   * @returns {Promise<TWorkspacePaginationInfo>} Promise resolving to a paginated list of workspaces
   * @throws {Error} If the API request fails
   */
  async list(nextPageCursor?: string): Promise<TWorkspacePaginationInfo> {
    return this.get(`/api/instances/workspaces/`, {
      params: {
        cursor: nextPageCursor,
      },
    })
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Checks if a workspace slug is available
   * @param {string} slug - The workspace slug to check
   * @returns {Promise<any>} Promise resolving to slug availability status
   * @throws {Error} If the API request fails
   */
  async slugCheck(slug: string): Promise<any> {
    const params = new URLSearchParams({ slug });
    return this.get(`/api/instances/workspace-slug-check/?${params.toString()}`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Creates a new workspace
   * @param {Partial<IWorkspace>} data - Workspace data for creation
   * @returns {Promise<IWorkspace>} Promise resolving to the created workspace
   * @throws {Error} If the API request fails
   */
  async create(data: Partial<IWorkspace>): Promise<IWorkspace> {
    return this.post("/api/instances/workspaces/", data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Lists workspaces currently held in 15-day trash
   */
  async listTrash(): Promise<any[]> {
    return this.get("/api/instances/workspaces/trash/")
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Restores a workspace from trash
   */
  async restoreWorkspace(workspaceId: string): Promise<any> {
    return this.post(`/api/instances/workspaces/${workspaceId}/restore/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Permanently purges a workspace from trash
   */
  async purgeWorkspace(workspaceId: string): Promise<any> {
    return this.delete(`/api/instances/workspaces/${workspaceId}/purge/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Resends onboarding credentials and temporary password email to customer admin
   */
  async resendHandover(workspaceId: string): Promise<any> {
    return this.post(`/api/instances/workspaces/${workspaceId}/resend-handover/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Lists all available backups for a given workspace
   */
  async listBackups(workspaceId: string): Promise<any[]> {
    return this.get(`/api/instances/workspaces/${workspaceId}/backups/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Creates an immediate backup for a workspace
   */
  async createBackup(workspaceId: string): Promise<any> {
    return this.post(`/api/instances/workspaces/${workspaceId}/backups/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Restores a workspace from a specific backup
   */
  async restoreBackup(workspaceId: string, backupId: string): Promise<any> {
    return this.post(`/api/instances/workspaces/${workspaceId}/backups/${backupId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  /**
   * Deletes a specific workspace backup
   */
  async deleteBackup(workspaceId: string, backupId: string): Promise<any> {
    return this.delete(`/api/instances/workspaces/${workspaceId}/backups/${backupId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}
