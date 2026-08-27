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
    <div className="font-sans flex h-full w-full flex-col overflow-hidden text-white">
      {/* Header Bar */}
      <div className="bg-neutral-950/40 flex items-center justify-between border-b border-white/10 px-5 py-3.5">
        <AIStreamStatus state={state} />

        <button
          type="button"
          onClick={onClose}
          aria-label="Close panel"
          className="text-neutral-400 hover:bg-neutral-800 flex size-7 items-center justify-center rounded-full transition-colors hover:text-white"
        >
          <X className="size-4" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="text-xs max-h-[360px] min-h-[200px] flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {messages.map((msg) => (
          <AIStreamMessage key={msg.id} message={msg} onConfirmAction={(actionText) => onSubmit(actionText)} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggestion Chips */}
      {messages.length <= 2 && state === "expanded" && (
        <div className="bg-neutral-950/20 border-t border-white/5 px-5 py-2">
          <div className="text-neutral-400 tracking-wider mb-2 text-[10px] font-semibold uppercase">Suggestions</div>
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => onSubmit(s.prompt)}
                className="bg-neutral-900/80 hover:bg-indigo-600/30 hover:border-indigo-500/50 text-neutral-300 text-xs flex cursor-pointer items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 transition-all hover:text-white"
              >
                <span>{s.icon || "✦"}</span>
                <span>{s.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Footer */}
      <div className="bg-neutral-950/60 border-t border-white/10 p-4">
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
