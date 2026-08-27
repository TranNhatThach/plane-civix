/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@plane/utils";
import type { AIStreamState } from "./types";

interface AIStreamStatusProps {
  state: AIStreamState;
  className?: string;
}

export const AIStreamStatus: React.FC<AIStreamStatusProps> = ({ state, className }) => {
  const isThinking = state === "thinking";
  const isStreaming = state === "streaming";

  return (
    <div className={cn("flex items-center gap-2 select-none", className)}>
      {/* Sparkle Icon */}
      <div className="relative flex items-center justify-center">
        <Sparkles
          className={cn(
            "text-violet-400 size-4 transition-transform duration-500",
            isThinking ? "text-indigo-300 animate-spin" : isStreaming ? "text-pink-400 scale-110" : "hover:rotate-12"
          )}
        />
        {(isThinking || isStreaming) && (
          <span className="bg-violet-500/30 absolute inset-0 animate-ping rounded-full blur-sm" />
        )}
      </div>

      {/* Status Label or Dot */}
      {isThinking ? (
        <div className="text-xs text-indigo-200 flex items-center gap-1 font-medium">
          <span>Thinking</span>
          <span className="flex gap-0.5">
            <span className="bg-indigo-300 size-1 animate-bounce rounded-full" style={{ animationDelay: "0ms" }} />
            <span className="bg-indigo-300 size-1 animate-bounce rounded-full" style={{ animationDelay: "150ms" }} />
            <span className="bg-indigo-300 size-1 animate-bounce rounded-full" style={{ animationDelay: "300ms" }} />
          </span>
        </div>
      ) : isStreaming ? (
        <span className="text-xs text-pink-300 animate-pulse font-medium">Generating...</span>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-xs text-neutral-200 font-medium tracking-wide">AI Stream</span>
          <span className="bg-emerald-400 size-1.5 animate-pulse rounded-full shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
        </div>
      )}
    </div>
  );
};
