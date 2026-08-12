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
        "group flex items-center justify-between gap-3 px-4 py-2 rounded-full cursor-pointer select-none",
        "bg-neutral-950/90 hover:bg-neutral-900/95 backdrop-blur-2xl border border-white/10 hover:border-white/20",
        "shadow-[0_10px_30px_rgba(0,0,0,0.5)] hover:shadow-[0_15px_35px_rgba(99,102,241,0.15)] transition-all duration-300",
        "w-[200px] h-[48px]",
        className
      )}
    >
      <div className="flex items-center gap-2.5 min-w-0">
        <div className="relative flex items-center justify-center">
          <Sparkles className="size-4 text-violet-400 group-hover:rotate-12 transition-transform duration-300" />
          <span className="absolute inset-0 rounded-full bg-violet-500/20 blur-xs animate-pulse" />
        </div>
        <span className="text-xs font-semibold text-white tracking-wide truncate">AI Stream</span>
      </div>

      <div className="flex items-center gap-1.5 shrink-0">
        <span className="size-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)] animate-pulse" />
        <span className="text-[10px] font-mono text-neutral-400 group-hover:text-white transition-colors">
          ⌘K
        </span>
      </div>
    </button>
  );
};
