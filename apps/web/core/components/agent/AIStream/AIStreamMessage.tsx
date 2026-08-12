/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { Sparkles, User, Check, X } from "lucide-react";
import { cn } from "@plane/utils";
import type { AIStreamMessageItem } from "./types";


interface AIStreamMessageProps {
  message: AIStreamMessageItem;
  onConfirmAction?: (actionText: string) => void;
}

export const AIStreamMessage: React.FC<AIStreamMessageProps> = ({ message, onConfirmAction }) => {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex gap-3 max-w-[90%] transition-all duration-300",
        isUser ? "ml-auto flex-row-reverse" : "mr-auto"
      )}
    >
      {/* Avatar Icon */}
      <div
        className={cn(
          "size-7 rounded-full flex items-center justify-center shrink-0 text-xs shadow-md border",
          isUser
            ? "bg-indigo-600 border-indigo-400 text-white"
            : "bg-neutral-900 border-neutral-700/60 text-violet-400"
        )}
      >
        {isUser ? <User className="size-3.5" /> : <Sparkles className="size-3.5" />}
      </div>

      {/* Bubble Content */}
      <div
        className={cn(
          "flex flex-col rounded-2xl px-4 py-3 text-xs leading-relaxed font-sans shadow-md border backdrop-blur-md",
          isUser
            ? "bg-indigo-600/90 border-indigo-500/40 text-white rounded-tr-xs"
            : "bg-neutral-900/90 border-white/10 text-neutral-200 rounded-tl-xs"
        )}
      >
        <div className="whitespace-pre-wrap">{message.content}</div>

        {/* HITL Confirmation Actions if needed */}
        {message.metadata?.requires_confirmation && (
          <div className="mt-3 pt-2.5 border-t border-white/10 flex items-center gap-2">
            <button
              type="button"
              onClick={() => onConfirmAction?.("Xác nhận thực hiện")}
              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center gap-1.5 shadow-sm transition"
            >
              <Check className="size-3.5" /> Xác nhận
            </button>
            <button
              type="button"
              onClick={() => onConfirmAction?.("Hủy bỏ thao tác")}
              className="px-3 py-1.5 rounded-lg bg-neutral-800 hover:bg-rose-600 text-neutral-300 hover:text-white font-medium text-xs flex items-center gap-1.5 shadow-sm transition"
            >
              <X className="size-3.5" /> Hủy
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
