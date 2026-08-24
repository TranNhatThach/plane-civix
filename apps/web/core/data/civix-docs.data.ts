/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import civixDocsRaw from "./civix-docs.json";

// ============================================================================
// CÁC KHUÔN MẪU TÀI LIỆU (DOCUMENTATION SCHEMAS & TEMPLATES)
// ============================================================================

export type DocIconType = "bot" | "building" | "file-text" | "git-branch" | "database" | "help-circle";

export interface IDocCallout {
  type: "tip" | "warning" | "note";
  text: string;
}

export interface IDocSubheading {
  title: string;
  body: string[];
  code?: string;
  callout?: IDocCallout;
}

export interface IDocContentBlock {
  heading: string;
  subheadings?: IDocSubheading[];
}

export interface IDocSection {
  id: string;
  version?: string;
  updatedAt?: string;
  title: string;
  badge?: string;
  iconName: DocIconType;
  description: string;
  content: IDocContentBlock[];
}

// ============================================================================
// DỮ LIỆU TÀI LIỆU LOAD TRỰC TIẾP TỪ JSON (JSON DATASET)
// ============================================================================

export const CIVIX_DOCS_SECTIONS: IDocSection[] = civixDocsRaw as IDocSection[];
