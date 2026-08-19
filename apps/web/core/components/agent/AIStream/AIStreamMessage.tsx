/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { Sparkles, User, Check, X } from "lucide-react";
import { cn } from "@plane/utils";
import type { AIStreamMessageItem } from "./types";
import { AIMarkdownRenderer } from "./AIMarkdownRenderer";

interface AIStreamMessageProps {
  message: AIStreamMessageItem;
  onConfirmAction?: (actionText: string) => void;
}

export const AIStreamMessage: React.FC<AIStreamMessageProps> = ({ message, onConfirmAction }) => {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex max-w-[90%] gap-3 transition-all duration-300",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
    >
      {/* Avatar Icon */}
      <div
        className={cn(
          "text-xs shadow-md flex size-7 shrink-0 items-center justify-center rounded-full border",
          isUser ? "bg-indigo-600 border-indigo-400 text-white" : "bg-neutral-900 border-neutral-700/60 text-violet-400"
        )}
      >
        {isUser ? <User className="size-3.5" /> : <Sparkles className="size-3.5" />}
      </div>

      {/* Bubble Content */}
      <div
        className={cn(
          "text-xs font-sans shadow-md flex flex-col rounded-2xl border px-4 py-3 leading-relaxed backdrop-blur-md",
          isUser
            ? "bg-indigo-600/90 border-indigo-500/40 rounded-tr-xs text-white"
            : "bg-neutral-900/90 text-neutral-200 rounded-tl-xs border-white/10"
        )}
      >
        <AIMarkdownRenderer content={message.content} isUser={isUser} />

        {/* HITL Confirmation Actions if needed */}
        {message.metadata?.requires_confirmation && (
          <div className="mt-3 flex items-center gap-2 border-t border-white/10 pt-2.5">
            <button
              type="button"
              onClick={() => onConfirmAction?.("Xác nhận thực hiện")}
              className="bg-emerald-600 hover:bg-emerald-500 text-xs shadow-sm flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium text-white transition"
            >
              <Check className="size-3.5" /> Xác nhận
            </button>
            <button
              type="button"
              onClick={() => onConfirmAction?.("Hủy bỏ thao tác")}
              className="bg-neutral-800 hover:bg-rose-600 text-neutral-300 text-xs shadow-sm flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition hover:text-white"
            >
              <X className="size-3.5" /> Hủy
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
