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
                      msg.id === assistantMsgId
                        ? { ...msg, content: accumulatedText, metadata: responseMeta }
                        : msg
                    )
                  );
                }
              } catch (e) {
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
                  content: `⚠️ Không thể kết nối với Plane AI Backend: ${
                    err?.message || "Server error"
                  }.`,
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
          "relative flex size-8 items-center justify-center rounded-md transition-all duration-200 border cursor-pointer select-none",
          isExpanded || isThinking || isListening
            ? "bg-indigo-600/30 border-indigo-500/60 text-indigo-300 shadow-md ring-2 ring-indigo-500/30"
            : "border-subtle-1 bg-layer-2 hover:bg-layer-1-hover text-placeholder hover:text-primary"
        )}
      >
        <span className="text-sm">✨</span>
        {isListening && (
          <span className="absolute -top-1 -right-1 size-2.5 rounded-full bg-pink-500 animate-ping" />
        )}
        {isThinking && (
          <span className="absolute -top-1 -right-1 size-2.5 rounded-full bg-indigo-500 animate-pulse" />
        )}
      </button>

      {/* Expanded Floating Glass Panel Dropdown */}
      {isExpanded && (
        <div className="absolute top-10 right-0 w-[480px] max-h-[560px] bg-neutral-900/95 backdrop-blur-2xl border border-neutral-700/70 shadow-2xl rounded-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-top-2 duration-300 z-50">
          {/* Header Bar */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-800 bg-neutral-950/60">
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-white flex items-center gap-1.5">
                <span className="text-indigo-400">✨</span> Plane AI Copilot
              </span>
              {isListening && (
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-purple-950/80 border border-purple-500/40">
                  <AudioWaveform active={true} />
                  <span className="text-[10px] text-purple-300 font-medium truncate max-w-[120px]">
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
                  "px-2.5 py-1 rounded-md text-[11px] font-medium transition flex items-center gap-1",
                  isListening
                    ? "bg-pink-600 text-white animate-bounce"
                    : "bg-neutral-800 text-neutral-300 hover:bg-neutral-700 hover:text-white"
                )}
              >
                🎙️ {isListening ? "Tắt" : "Mic"}
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("Tổng hợp báo cáo Standup 24h qua")}
                className="text-[11px] px-2 py-1 rounded-md bg-neutral-800 text-neutral-300 hover:bg-indigo-600 hover:text-white transition"
              >
                📊 Standup
              </button>
              <button
                type="button"
                onClick={() => handleSendMessage("Đề xuất kế hoạch Sprint tiếp theo")}
                className="text-[11px] px-2 py-1 rounded-md bg-neutral-800 text-neutral-300 hover:bg-purple-600 hover:text-white transition"
              >
                🚀 Sprint
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[220px] max-h-[360px] text-xs">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "flex flex-col max-w-[88%] rounded-xl p-3 shadow-md transition-all",
                  msg.role === "user"
                    ? "ml-auto bg-indigo-600 text-white rounded-br-none"
                    : "mr-auto bg-neutral-800/90 border border-neutral-700/50 text-neutral-100 rounded-bl-none"
                )}
              >
                <div className="whitespace-pre-wrap leading-relaxed font-sans">{msg.content}</div>

                {/* HITL Interactive Buttons if confirmation is required */}
                {msg.metadata?.requires_confirmation && (
                  <div className="mt-3 pt-2 border-t border-neutral-700/60 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleSendMessage("Xác nhận thực hiện điều chuyển ngay")}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs flex items-center gap-1 shadow-sm transition"
                    >
                      ✅ Xác nhận thực hiện
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSendMessage("Hủy bỏ thao tác")}
                      className="px-3 py-1.5 rounded-lg bg-neutral-700 hover:bg-rose-600 text-white font-medium text-xs flex items-center gap-1 shadow-sm transition"
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
          <div className="p-3 border-t border-neutral-800 bg-neutral-950/60 flex items-center gap-2">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
              placeholder="Nhập yêu cầu hoặc nói bằng giọng nói..."
              className="flex-1 bg-neutral-800/80 border border-neutral-700/60 text-white placeholder-neutral-400 text-xs rounded-xl px-3.5 py-2.5 outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
            <button
              type="button"
              onClick={() => handleSendMessage()}
              disabled={isThinking || !inputText.trim()}
              className="px-4 py-2.5 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:opacity-50 text-white font-semibold text-xs rounded-xl transition shadow-md flex items-center gap-1"
            >
              Gửi 🚀
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
