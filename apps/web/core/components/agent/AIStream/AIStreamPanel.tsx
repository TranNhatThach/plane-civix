/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useRef, useEffect } from "react";
import { X, Sparkles } from "lucide-react";
import type { AIStreamState, AIStreamMessageItem, SuggestionChip } from "./types";

import { AIStreamMessage } from "./AIStreamMessage";
import { AIStreamInput } from "./AIStreamInput";
import { AIStreamStatus } from "./AIStreamStatus";

interface AIStreamPanelProps {
  state: AIStreamState;
  input: string;
  setInput: (val: string) => void;
  messages: AIStreamMessageItem[];
  suggestions: SuggestionChip[];
  onClose: () => void;
  onSubmit: (prompt?: string) => void;
  isListening?: boolean;
  onToggleListening?: () => void;
  inputRef?: React.Ref<HTMLTextAreaElement>;
}

export const AIStreamPanel: React.FC<AIStreamPanelProps> = ({
  state,
  input,
  setInput,
  messages,
  suggestions,
  onClose,
  onSubmit,
  isListening,
  onToggleListening,
  inputRef,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, state]);

  return (
    <div className="flex flex-col w-full h-full text-white font-sans overflow-hidden">
      {/* Header Bar */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/10 bg-neutral-950/40">
        <AIStreamStatus state={state} />

        <button
          type="button"
          onClick={onClose}
          aria-label="Close panel"
          className="size-7 rounded-full flex items-center justify-center text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 min-h-[200px] max-h-[360px] text-xs">
        {messages.map((msg) => (
          <AIStreamMessage
            key={msg.id}
            message={msg}
            onConfirmAction={(actionText) => onSubmit(actionText)}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      {messages.length <= 2 && state === "expanded" && (
        <div className="px-5 py-2 border-t border-white/5 bg-neutral-950/20">
          <div className="text-[10px] font-semibold text-neutral-400 uppercase tracking-wider mb-2">
            Suggestions
          </div>
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSubmit(s.prompt)}
                className="px-3 py-1.5 rounded-xl bg-neutral-900/80 hover:bg-indigo-600/30 hover:border-indigo-500/50 border border-white/10 text-neutral-300 hover:text-white text-xs transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <span>{s.icon || "✦"}</span>
                <span>{s.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Footer */}
      <div className="p-4 border-t border-white/10 bg-neutral-950/60">
        <AIStreamInput
          input={input}
          setInput={setInput}
          onSubmit={() => onSubmit()}
          isListening={isListening}
          onToggleListening={onToggleListening}
          disabled={state === "thinking" || state === "streaming"}
          inputRef={inputRef}
        />
      </div>
    </div>
  );
};
