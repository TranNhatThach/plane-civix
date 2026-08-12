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
            "size-4 text-violet-400 transition-transform duration-500",
            isThinking ? "animate-spin text-indigo-300" : isStreaming ? "scale-110 text-pink-400" : "hover:rotate-12"
          )}
        />
        {(isThinking || isStreaming) && (
          <span className="absolute inset-0 rounded-full bg-violet-500/30 blur-sm animate-ping" />
        )}
      </div>

      {/* Status Label or Dot */}
      {isThinking ? (
        <div className="flex items-center gap-1 text-xs font-medium text-indigo-200">
          <span>Thinking</span>
          <span className="flex gap-0.5">
            <span className="size-1 rounded-full bg-indigo-300 animate-bounce" style={{ animationDelay: "0ms" }} />
            <span className="size-1 rounded-full bg-indigo-300 animate-bounce" style={{ animationDelay: "150ms" }} />
            <span className="size-1 rounded-full bg-indigo-300 animate-bounce" style={{ animationDelay: "300ms" }} />
          </span>
        </div>
      ) : isStreaming ? (
        <span className="text-xs font-medium text-pink-300 animate-pulse">Generating...</span>
      ) : (
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-neutral-200 tracking-wide">AI Stream</span>
          <span className="size-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse" />
        </div>
      )}
    </div>
  );
};
