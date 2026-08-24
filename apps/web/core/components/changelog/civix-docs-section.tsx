/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import {
  Bot,
  Building2,
  FileText,
  GitBranch,
  Database,
  HelpCircle,
  Copy,
  Check,
  AlertCircle,
  Lightbulb,
  Hash,
  Terminal,
  ChevronRight,
  Calendar,
  Tag,
  Clock,
} from "lucide-react";
import { CIVIX_DOCS_SECTIONS } from "@/data/civix-docs.data";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  bot: Bot,
  building: Building2,
  "file-text": FileText,
  "git-branch": GitBranch,
  database: Database,
  "help-circle": HelpCircle,
};

export function CivixDocsSection() {
  const [activeSectionId, setActiveSectionId] = useState<string>(CIVIX_DOCS_SECTIONS[0].id);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const handleCopyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => {
      setCopiedCode(null);
    }, 2000);
  };

  return (
    <div className="flex w-full flex-col gap-6">
      {/* Docs Milestones Navigation Pills */}
      <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-4">
        {CIVIX_DOCS_SECTIONS.map((sec) => {
          const Icon = ICON_MAP[sec.iconName] || FileText;
          const isActive = activeSectionId === sec.id;

          return (
            <button
              key={sec.id}
              type="button"
              onClick={() => setActiveSectionId(sec.id)}
              className={`flex flex-col items-start justify-between gap-2 rounded-xl border p-3 text-left transition-all ${
                isActive
                  ? "border-custom-primary-100 bg-custom-primary-100/10 text-custom-primary-100 shadow-sm ring-custom-primary-100/30 ring-1"
                  : "border-custom-border-200 bg-custom-background-100 text-custom-text-200 hover:border-custom-border-300 hover:bg-custom-background-90 hover:text-custom-text-100"
              }`}
            >
              <div className="flex w-full items-center justify-between">
                <div
                  className={`flex h-7 w-7 items-center justify-center rounded-lg ${isActive ? "bg-custom-primary-100 text-white" : "bg-custom-background-90 text-custom-text-200"}`}
                >
                  <Icon className="h-4 w-4" />
                </div>
                {sec.version && (
                  <span
                    className={`rounded-md border px-1.5 py-0.5 text-[10px] font-bold ${isActive ? "border-custom-primary-100/40 bg-custom-primary-100/20 text-custom-primary-100" : "border-custom-border-200 bg-custom-background-90 text-custom-text-300"}`}
                  >
                    {sec.version}
                  </span>
                )}
              </div>

              <div>
                <span className="text-xs text-custom-text-100 line-clamp-1 font-semibold">{sec.title}</span>
                {sec.updatedAt && (
                  <div className="text-custom-text-300 mt-0.5 flex items-center gap-1 text-[10px] font-medium">
                    <Clock className="h-2.5 w-2.5" />
                    <span>{sec.updatedAt}</span>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Section Details */}
      {CIVIX_DOCS_SECTIONS.map((sec) => {
        if (sec.id !== activeSectionId) return null;
        const Icon = ICON_MAP[sec.iconName] || FileText;

        return (
          <article
            key={sec.id}
            id={sec.id}
            className="border-custom-border-200 bg-custom-background-100 shadow-sm flex flex-col rounded-2xl border p-6 sm:p-8"
          >
            {/* Header with Timeline Metadata */}
            <div className="border-custom-border-200 mb-6 flex flex-wrap items-start justify-between gap-4 border-b pb-5">
              <div className="flex items-start gap-3.5">
                <div className="bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border">
                  <Icon className="h-6 w-6" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="text-xl sm:text-2xl text-custom-text-100 font-bold tracking-tight">{sec.title}</h2>
                    {sec.version && (
                      <span className="bg-custom-primary-100 text-xs shadow-xs inline-flex items-center gap-1 rounded-md px-2 py-0.5 font-bold text-white">
                        <Tag className="h-3 w-3" />
                        {sec.version}
                      </span>
                    )}
                    {sec.badge && (
                      <span className="bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 inline-block rounded-full border px-2.5 py-0.5 text-[11px] font-medium">
                        {sec.badge}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 flex items-center gap-2">
                    {sec.updatedAt && (
                      <span className="text-xs text-custom-text-300 inline-flex items-center gap-1 font-medium">
                        <Calendar className="h-3.5 w-3.5" />
                        Mốc thời gian cập nhật: {sec.updatedAt}
                      </span>
                    )}
                  </div>
                  <p className="text-xs sm:text-sm text-custom-text-200 mt-2 leading-relaxed">{sec.description}</p>
                </div>
              </div>
            </div>

            {/* Content Blocks */}
            <div className="space-y-8">
              {sec.content.map((block) => (
                <div key={block.heading} className="space-y-4">
                  <h3 className="text-base sm:text-lg text-custom-text-100 flex items-center gap-2 font-bold">
                    <Hash className="text-custom-primary-100 h-4 w-4 shrink-0" />
                    <span>{block.heading}</span>
                  </h3>

                  {block.subheadings && (
                    <div className="space-y-4 pl-1 sm:pl-3">
                      {block.subheadings.map((sub) => {
                        const codeBlockId = `${sec.id}-${block.heading}-${sub.title}`;
                        const isCopied = copiedCode === codeBlockId;

                        return (
                          <div
                            key={sub.title}
                            className="bg-custom-background-90/70 border-custom-border-200/80 rounded-xl border p-4 sm:p-5"
                          >
                            <h4 className="text-sm text-custom-text-100 mb-2 flex items-center gap-2 font-semibold">
                              <ChevronRight className="text-custom-primary-100 h-3.5 w-3.5 shrink-0" />
                              <span>{sub.title}</span>
                            </h4>
                            <div className="space-y-2">
                              {sub.body.map((p) => (
                                <p key={p} className="text-xs sm:text-sm text-custom-text-200 leading-relaxed">
                                  {p}
                                </p>
                              ))}
                            </div>

                            {/* Callout */}
                            {sub.callout && (
                              <div
                                className={`text-xs mt-3 flex items-start gap-2.5 rounded-lg border p-3 leading-relaxed ${
                                  sub.callout.type === "warning"
                                    ? "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20"
                                    : "bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20"
                                }`}
                              >
                                {sub.callout.type === "warning" ? (
                                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                                ) : (
                                  <Lightbulb className="mt-0.5 h-4 w-4 shrink-0" />
                                )}
                                <span>{sub.callout.text}</span>
                              </div>
                            )}

                            {/* Code snippet block */}
                            {sub.code && (
                              <div className="border-custom-border-200 bg-custom-background-100 relative mt-3.5 overflow-hidden rounded-lg border">
                                <div className="border-custom-border-200 bg-custom-background-90 flex items-center justify-between border-b px-3.5 py-1.5">
                                  <div className="font-mono text-custom-text-300 flex items-center gap-1.5 text-[11px] font-medium">
                                    <Terminal className="h-3 w-3" />
                                    <span>Ví dụ / Command Line</span>
                                  </div>
                                  <button
                                    type="button"
                                    onClick={() => handleCopyCode(sub.code!, codeBlockId)}
                                    className="text-xs text-custom-text-300 hover:text-custom-text-100 inline-flex items-center gap-1 font-medium transition-colors"
                                  >
                                    {isCopied ? (
                                      <>
                                        <Check className="text-emerald-500 h-3 w-3" />
                                        <span className="text-emerald-500 text-[11px]">Đã chép</span>
                                      </>
                                    ) : (
                                      <>
                                        <Copy className="h-3 w-3" />
                                        <span className="text-[11px]">Sao chép</span>
                                      </>
                                    )}
                                  </button>
                                </div>
                                <pre className="font-mono text-xs text-custom-text-100 overflow-x-auto p-3.5 leading-relaxed whitespace-pre">
                                  <code>{sub.code}</code>
                                </pre>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </article>
        );
      })}
    </div>
  );
}
