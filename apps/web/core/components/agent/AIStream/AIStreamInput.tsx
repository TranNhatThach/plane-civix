/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { ArrowUp, Mic } from "lucide-react";
import { cn } from "@plane/utils";

interface AIStreamInputProps {
  input: string;
  setInput: (val: string) => void;
  onSubmit: () => void;
  isListening?: boolean;
  onToggleListening?: () => void;
  disabled?: boolean;
  inputRef?: React.Ref<HTMLTextAreaElement>;
}

export const AIStreamInput: React.FC<AIStreamInputProps> = ({
  input,
  setInput,
  onSubmit,
  isListening = false,
  onToggleListening,
  disabled = false,
  inputRef,
}) => {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="relative flex items-center w-full rounded-2xl bg-neutral-900/90 border border-white/10 p-1.5 transition-all focus-within:border-indigo-500/50 focus-within:ring-2 focus-within:ring-indigo-500/20 shadow-inner">
      <textarea
        ref={inputRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything..."
        disabled={disabled}
        className="w-full bg-transparent px-3 py-2 text-xs text-white placeholder-neutral-400 outline-none resize-none min-h-[36px] max-h-[120px] font-sans"
      />

      <div className="flex items-center gap-1.5 shrink-0 pr-1">
        {/* Voice Speech Mic Button */}
        {onToggleListening && (
          <button
            type="button"
            onClick={onToggleListening}
            title={isListening ? "Stop Listening" : "Voice Speech (vi-VN)"}
            className={cn(
              "size-7 rounded-xl flex items-center justify-center transition-all text-xs",
              isListening
                ? "bg-pink-600 text-white animate-bounce shadow-md shadow-pink-500/30"
                : "text-neutral-400 hover:text-white hover:bg-neutral-800"
            )}
          >
            <Mic className="size-3.5" />
          </button>
        )}

        {/* Submit Arrow Button */}
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !input.trim()}
          aria-label="Submit prompt"
          className={cn(
            "size-7 rounded-xl flex items-center justify-center transition-all font-semibold",
            input.trim() && !disabled
              ? "bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-500/20 cursor-pointer"
              : "bg-neutral-800 text-neutral-500 cursor-not-allowed"
          )}
        >
          <ArrowUp className="size-4" />
        </button>
      </div>
    </div>
  );
};
