/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { Sparkles } from "lucide-react";
import { cn } from "@plane/utils";
import type { AIStreamState } from "./types";

interface AIStreamButtonProps {
  state: AIStreamState;
  onClick: () => void;
  className?: string;
}

export const AIStreamButton: React.FC<AIStreamButtonProps> = ({ state, onClick, className }) => {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Open AI Stream Assistant"
      className={cn(
        "group flex cursor-pointer items-center justify-between gap-3 rounded-full px-4 py-2 select-none",
        "bg-neutral-950/90 hover:bg-neutral-900/95 border border-white/10 backdrop-blur-2xl hover:border-white/20",
        "shadow-[0_10px_30px_rgba(0,0,0,0.5)] transition-all duration-300 hover:shadow-[0_15px_35px_rgba(99,102,241,0.15)]",
        "h-[48px] w-[200px]",
        className
      )}
    >
      <div className="flex min-w-0 items-center gap-2.5">
        <div className="relative flex items-center justify-center">
          <Sparkles className="text-violet-400 size-4 transition-transform duration-300 group-hover:rotate-12" />
          <span className="bg-violet-500/20 absolute inset-0 animate-pulse rounded-full blur-xs" />
        </div>
        <span className="text-xs truncate font-semibold tracking-wide text-white">AI Stream</span>
      </div>

      <div className="flex shrink-0 items-center gap-1.5">
        <span className="bg-emerald-400 size-2 animate-pulse rounded-full shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
        <span className="font-mono text-neutral-400 text-[10px] transition-colors group-hover:text-white">⌘K</span>
      </div>
    </button>
  );
};
