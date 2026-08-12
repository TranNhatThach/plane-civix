/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

export type AIStreamState = "collapsed" | "expanded" | "thinking" | "streaming";

export interface AIStreamMessageItem {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
  metadata?: {
    action_taken?: string;
    requires_confirmation?: boolean;
    pending_action?: any;
    data?: any;
  };
}

export interface SuggestionChip {
  id: string;
  label: string;
  prompt: string;
  icon?: string;
}

export interface AIStreamOptions {
  workspaceSlug?: string;
  projectId?: string;
  activeIssueId?: string;
  onStateChange?: (state: AIStreamState) => void;
}
