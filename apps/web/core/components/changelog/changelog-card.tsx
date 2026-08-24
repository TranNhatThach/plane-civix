/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import { Sparkles, Bug, Zap, Bot, ShieldCheck, Tag, Calendar, CheckCircle2, Share2, Check } from "lucide-react";
import type { IReleaseChangelog } from "@/data/civix-changelog.data";

interface Props {
  release: IReleaseChangelog;
}

const TYPE_CONFIG = {
  feature: {
    label: "Tính năng mới",
    icon: Sparkles,
    badgeBg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
    dotBg: "bg-emerald-500",
  },
  fix: {
    label: "Sửa lỗi (Bug Fix)",
    icon: Bug,
    badgeBg: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20",
    dotBg: "bg-rose-500",
  },
  improvement: {
    label: "Cải tiến",
    icon: Zap,
    badgeBg: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
    dotBg: "bg-amber-500",
  },
  agent: {
    label: "AI Agent & Bot",
    icon: Bot,
    badgeBg: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
    dotBg: "bg-blue-500",
  },
  security: {
    label: "Bảo mật",
    icon: ShieldCheck,
    badgeBg: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20",
    dotBg: "bg-purple-500",
  },
};

export function ChangelogCard({ release }: Props) {
  const [copiedLink, setCopiedLink] = useState(false);
  const releaseAnchorId = `release-${release.version.replace(/\./g, "-")}`;

  const handleCopyLink = () => {
    const url = `${window.location.origin}/changelog#${releaseAnchorId}`;
    navigator.clipboard.writeText(url);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  return (
    <article
      id={releaseAnchorId}
      className="group border-custom-border-200 bg-custom-background-100 shadow-sm hover:border-custom-border-300 hover:shadow-md relative mb-8 flex scroll-mt-24 flex-col rounded-2xl border p-6 transition-all duration-200 sm:p-8"
    >
      {/* Top Meta Bar */}
      <div className="border-custom-border-200/80 mb-5 flex flex-wrap items-center justify-between gap-3 border-b pb-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="text-sm bg-custom-primary-100 shadow-xs inline-flex items-center gap-1.5 rounded-lg px-3 py-1 font-bold text-white">
            <Tag className="h-3.5 w-3.5" />
            {release.version}
          </span>
          {release.isLatest && (
            <span className="text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-semibold">
              <span className="bg-emerald-500 h-1.5 w-1.5 animate-pulse rounded-full" />
              {release.badgeText || "Bản mới nhất"}
            </span>
          )}
          <span className="text-xs text-custom-text-300 inline-flex items-center gap-1.5 font-medium">
            <Calendar className="h-3.5 w-3.5" />
            {release.releaseDate}
          </span>
        </div>

        {/* Copy / Share Button */}
        <button
          type="button"
          onClick={handleCopyLink}
          title="Sao chép liên kết phiên bản này"
          className="text-xs text-custom-text-300 hover:text-custom-text-100 hover:bg-custom-background-90 border-custom-border-200 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 transition-colors"
        >
          {copiedLink ? (
            <>
              <Check className="text-emerald-500 h-3.5 w-3.5" />
              <span className="text-emerald-500 font-medium">Đã chép link</span>
            </>
          ) : (
            <>
              <Share2 className="h-3.5 w-3.5" />
              <span>Chia sẻ</span>
            </>
          )}
        </button>
      </div>

      {/* Release Title & Summary */}
      <h2 className="text-xl sm:text-2xl text-custom-text-100 mb-2 font-bold tracking-tight">{release.title}</h2>
      <p className="text-sm sm:text-base text-custom-text-200 mb-6 leading-relaxed">{release.summary}</p>

      {/* Highlights Box */}
      {release.highlights && release.highlights.length > 0 && (
        <div className="bg-custom-background-90/80 border-custom-border-200/80 mb-6 rounded-xl border p-4 sm:p-5">
          <div className="text-custom-primary-100 tracking-wider mb-3 flex items-center gap-1.5 text-[11px] font-bold uppercase">
            <Sparkles className="h-3.5 w-3.5" />
            Điểm nhấn quan trọng
          </div>
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {release.highlights.map((hl) => (
              <div
                key={`${release.version}-${hl.slice(0, 30)}`}
                className="bg-custom-background-100/90 border-custom-border-100/80 text-xs text-custom-text-100 flex items-start gap-2.5 rounded-lg border p-2.5"
              >
                <CheckCircle2 className="text-custom-primary-100 mt-0.5 h-4 w-4 shrink-0" />
                <span className="leading-snug">{hl}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Items */}
      <div className="space-y-3">
        <div className="text-xs text-custom-text-300 tracking-wider mb-2 font-semibold uppercase">
          Chi tiết thay đổi & bản vá ({release.items.length})
        </div>
        {release.items.map((item) => {
          const cfg = TYPE_CONFIG[item.type] || TYPE_CONFIG.improvement;
          const Icon = cfg.icon;

          return (
            <div
              key={`${release.version}-${item.type}-${item.title}`}
              className="border-custom-border-200/60 bg-custom-background-90/50 hover:bg-custom-background-90 hover:border-custom-border-200 flex items-start gap-3.5 rounded-xl border p-3.5 transition-colors"
            >
              <div className={`mt-0.5 flex shrink-0 items-center justify-center rounded-lg border p-2 ${cfg.badgeBg}`}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className="text-xs sm:text-sm text-custom-text-100 font-semibold">{item.title}</span>
                  <span
                    className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-semibold ${cfg.badgeBg}`}
                  >
                    {cfg.label}
                  </span>
                </div>
                {item.description && <p className="text-xs text-custom-text-300 leading-relaxed">{item.description}</p>}
              </div>
            </div>
          );
        })}
      </div>
    </article>
  );
}
