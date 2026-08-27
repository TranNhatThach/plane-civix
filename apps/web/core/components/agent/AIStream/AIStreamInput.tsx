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
    <div className="bg-neutral-900/90 focus-within:border-indigo-500/50 focus-within:ring-indigo-500/20 shadow-inner relative flex w-full items-center rounded-2xl border border-white/10 p-1.5 transition-all focus-within:ring-2">
      <textarea
        ref={inputRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything..."
        disabled={disabled}
        className="text-xs placeholder-neutral-400 font-sans max-h-[120px] min-h-[36px] w-full resize-none bg-transparent px-3 py-2 text-white outline-none"
      />

      <div className="flex shrink-0 items-center gap-1.5 pr-1">
        {/* Voice Speech Mic Button */}
        {onToggleListening && (
          <button
            type="button"
            onClick={onToggleListening}
            title={isListening ? "Stop Listening" : "Voice Speech (vi-VN)"}
            className={cn(
              "text-xs flex size-7 items-center justify-center rounded-xl transition-all",
              isListening
                ? "bg-pink-600 shadow-md shadow-pink-500/30 animate-bounce text-white"
                : "text-neutral-400 hover:bg-neutral-800 hover:text-white"
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
            "flex size-7 items-center justify-center rounded-xl font-semibold transition-all",
            input.trim() && !disabled
              ? "bg-indigo-600 hover:bg-indigo-500 shadow-md shadow-indigo-500/20 cursor-pointer text-white"
              : "bg-neutral-800 text-neutral-500 cursor-not-allowed"
          )}
        >
          <ArrowUp className="size-4" />
        </button>
      </div>
    </div>
  );
};
