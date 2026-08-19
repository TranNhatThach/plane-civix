/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { cn } from "@plane/utils";
import { useVoiceRecognition } from "@/helpers/use-voice-recognition";
import { AudioWaveform } from "./audio-waveform";
import { AIMarkdownRenderer } from "./AIStream/AIMarkdownRenderer";

interface AgentMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: any;
}

export const DynamicIslandAgent: React.FC = () => {
  const params = useParams();
  const workspaceSlug = (params?.slug as string) || "default";
  const projectId = params?.projectId as string | undefined;

  const [isExpanded, setIsExpanded] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [inputText, setInputText] = useState("");
  const [messages, setMessages] = useState<AgentMessageItem[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "👋 Xin chào! Em là **Plane AI Copilot**. Em có thể giúp anh/chị tạo task tự động, kiểm tra trùng lặp, lập kế hoạch Sprint, hoặc tổng hợp báo cáo Standup!",
    },
  ]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Voice Speech Recognition Hook
  const { isListening, transcript, toggleListening } = useVoiceRecognition({
    lang: "vi-VN",
    onResult: (text) => {
      setInputText(text);
    },
  });

  useEffect(() => {
    if (transcript) {
      setInputText(transcript);
    }
  }, [transcript]);

  // Click outside to collapse
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsExpanded(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    if (isExpanded) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isExpanded]);

  const handleSendMessage = useCallback(
    async (customText?: string) => {
      const query = (customText || inputText).trim();
      if (!query || isThinking) return;

      setInputText("");
      setIsExpanded(true);
      setIsThinking(true);

      const userMsgId = `user-${Date.now()}`;
      const assistantMsgId = `assistant-${Date.now()}`;

      setMessages((prev) => [
        ...prev,
        { id: userMsgId, role: "user", content: query },
        { id: assistantMsgId, role: "assistant", content: "..." },
      ]);

      try {
        const response = await fetch(`/api/workspaces/${workspaceSlug}/agent/chat/stream/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: query,
            session_id: sessionId,
            active_project_id: projectId,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error("HTTP error " + response.status);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = "";
        let responseMeta: any = {};

        while (true) {
          // eslint-disable-next-line no-await-in-loop
          const { value, done } = await reader.read();
          if (done) break;

          const chunkText = decoder.decode(value);
          const lines = chunkText.split("\n\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.substring(6));
                if (data.event === "start") {
                  if (data.session_id) setSessionId(data.session_id);
                  responseMeta = data;
                } else if (data.event === "chunk") {
                  accumulatedText += data.content;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === assistantMsgId ? { ...msg, content: accumulatedText, metadata: responseMeta } : msg
                    )
                  );
                }
              } catch {
                // fallback raw text parsing
              }
            }
          }
        }
      } catch (err: any) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: `⚠️ Không thể kết nối với Plane AI Backend: ${err?.message || "Server error"}.`,
                }
              : msg
          )
        );
      } finally {
        setIsThinking(false);
      }
    },
    [inputText, isThinking, workspaceSlug, sessionId, projectId]
  );

  return (
    <div ref={containerRef} className="relative z-50 flex items-center">
      {/* Sleek Top Header Icon Trigger Button */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        title="Plane AI Copilot"
        className={cn(
          "relative flex size-8 cursor-pointer items-center justify-center rounded-md border transition-all duration-200 select-none",
          isExpanded || isThinking || isListening
            ? "bg-indigo-600/30 border-indigo-500/60 text-indigo-300 shadow-md ring-indigo-500/30 ring-2"
            : "border-subtle-1 bg-layer-2 text-placeholder hover:bg-layer-1-hover hover:text-primary"
        )}
      >
        <span className="text-sm">✨</span>
        {isListening && <span className="bg-pink-500 absolute -top-1 -right-1 size-2.5 animate-ping rounded-full" />}
        {isThinking && <span className="bg-indigo-500 absolute -top-1 -right-1 size-2.5 animate-pulse rounded-full" />}
      </button>

      {/* Expanded Floating Glass Panel Dropdown */}
      {isExpanded && (
        <div className="bg-neutral-900/95 border-neutral-700/70 shadow-2xl animate-in fade-in slide-in-from-top-2 absolute top-10 right-0 z-50 flex max-h-[560px] w-[480px] flex-col overflow-hidden rounded-2xl border backdrop-blur-2xl duration-300">
          {/* Header Bar */}
          <div className="border-neutral-800 bg-neutral-950/60 flex items-center justify-between border-b px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="text-sm flex items-center gap-1.5 font-bold text-white">
                <span className="text-indigo-400">✨</span> Plane AI Copilot
              </span>
              {isListening && (
                <div className="bg-purple-950/80 border-purple-500/40 flex items-center gap-1.5 rounded-full border px-2 py-0.5">
                  <AudioWaveform active={true} />
                  <span className="text-purple-300 max-w-[120px] truncate text-[10px] font-medium">
                    {transcript || "Đang nghe..."}
                  </span>
                </div>
              )}
            </div>

            {/* Quick Action Chips */}
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={toggleListening}
                title={isListening ? "Tắt Micro" : "Bật Micro"}
                className={cn(
                  "flex items-center gap-1 rounded-md px-2.5 py-1 text-[11px] font-medium transition",
                  isListening
                    ? "bg-pink-600 animate-bounce text-white"
                    : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700 hover:text-white"
                )}
              >
                🎙️ {isListening ? "Tắt" : "Mic"}
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("Tổng hợp báo cáo Standup 24h qua")}
                className="bg-neutral-800 text-neutral-300 hover:bg-indigo-600 rounded-md px-2 py-1 text-[11px] transition hover:text-white"
              >
                📊 Standup
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("Đề xuất kế hoạch Sprint tiếp theo")}
                className="bg-neutral-800 text-neutral-300 hover:bg-purple-600 rounded-md px-2 py-1 text-[11px] transition hover:text-white"
              >
                🚀 Sprint
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="text-xs max-h-[360px] min-h-[220px] flex-1 space-y-3 overflow-y-auto p-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "shadow-md flex max-w-[88%] flex-col rounded-xl p-3 transition-all",
                  msg.role === "user"
                    ? "bg-indigo-600 ml-auto rounded-br-none text-white"
                    : "bg-neutral-800/90 border-neutral-700/50 text-neutral-100 mr-auto rounded-bl-none border"
                )}
              >
                <AIMarkdownRenderer content={msg.content} isUser={msg.role === "user"} />

                {/* HITL Interactive Buttons if confirmation is required */}
                {msg.metadata?.requires_confirmation && (
                  <div className="border-neutral-700/60 mt-3 flex items-center gap-2 border-t pt-2">
                    <button
                      type="button"
                      onClick={() => handleSendMessage("Xác nhận thực hiện điều chuyển ngay")}
                      className="bg-emerald-600 hover:bg-emerald-500 text-xs shadow-sm flex items-center gap-1 rounded-lg px-3 py-1.5 font-medium text-white transition"
                    >
                      ✅ Xác nhận thực hiện
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSendMessage("Hủy bỏ thao tác")}
                      className="bg-neutral-700 hover:bg-rose-600 text-xs shadow-sm flex items-center gap-1 rounded-lg px-3 py-1.5 font-medium text-white transition"
                    >
                      ❌ Hủy bỏ
                    </button>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Footer */}
          <div className="border-neutral-800 bg-neutral-950/60 flex items-center gap-2 border-t p-3">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Nhập yêu cầu hoặc nói bằng giọng nói..."
              className="bg-neutral-800/80 border-neutral-700/60 placeholder-neutral-400 text-xs focus:border-indigo-500 focus:ring-indigo-500 flex-1 rounded-xl border px-3.5 py-2.5 text-white transition outline-none focus:ring-1"
            />
            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={isThinking || !inputText.trim()}
              className="from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-xs shadow-md flex items-center gap-1 rounded-xl bg-gradient-to-r px-4 py-2.5 font-semibold text-white transition disabled:opacity-50"
            >
              Gửi 🚀
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
