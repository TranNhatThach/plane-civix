/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React from "react";
import { Sparkles, Bug, Zap, Bot, ShieldCheck, Tag, Calendar, CheckCircle2 } from "lucide-react";
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
  return (
    <div className="border-custom-border-200 dark:border-custom-border-300 relative border-l pb-10 pl-8 last:border-l-transparent last:pb-0 md:pl-10">
      {/* Timeline Node Dot */}
      <div className="border-custom-background-100 bg-custom-primary-100 shadow-sm absolute top-1 -left-[9px] flex h-[18px] w-[18px] items-center justify-center rounded-full border-4" />

      {/* Header Info */}
      <div className="mb-2 flex flex-wrap items-center gap-2.5">
        <span className="text-sm bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-semibold">
          <Tag className="h-3.5 w-3.5" />
          {release.version}
        </span>
        {release.isLatest && (
          <span className="text-xs bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20 inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 font-medium">
            <CheckCircle2 className="h-3 w-3" />
            {release.badgeText || "Mới nhất"}
          </span>
        )}
        <span className="text-xs text-custom-text-300 ml-auto inline-flex items-center gap-1">
          <Calendar className="h-3.5 w-3.5" />
          {release.releaseDate}
        </span>
      </div>

      {/* Release Title & Summary */}
      <h3 className="text-lg text-custom-text-100 mb-1.5 font-bold">{release.title}</h3>
      <p className="text-sm text-custom-text-200 mb-4 leading-relaxed">{release.summary}</p>

      {/* Highlights Box */}
      {release.highlights && release.highlights.length > 0 && (
        <div className="bg-custom-background-90 border-custom-border-200 mb-4 rounded-lg border p-3.5">
          <div className="text-xs text-custom-text-300 tracking-wider mb-2 font-semibold uppercase">
            Điểm nổi bật của phiên bản
          </div>
          <ul className="space-y-1.5">
            {release.highlights.map((hl) => (
              <li
                key={`${release.version}-${hl.slice(0, 30)}`}
                className="text-xs text-custom-text-100 flex items-start gap-2"
              >
                <span className="text-custom-primary-100 mt-0.5 font-bold">•</span>
                <span>{hl}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed Items */}
      <div className="space-y-3">
        {release.items.map((item) => {
          const cfg = TYPE_CONFIG[item.type] || TYPE_CONFIG.improvement;
          const Icon = cfg.icon;

          return (
            <div
              key={`${release.version}-${item.type}-${item.title}`}
              className="border-custom-border-100/60 bg-custom-background-100 shadow-xs hover:border-custom-border-200 flex items-start gap-3 rounded-lg border p-3 transition-colors"
            >
              <div
                className={`mt-0.5 flex shrink-0 items-center justify-center rounded-md border p-1.5 ${cfg.badgeBg}`}
              >
                <Icon className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-0.5 flex flex-wrap items-center gap-2">
                  <span className="text-xs text-custom-text-100 font-semibold">{item.title}</span>
                  <span className={`inline-block rounded border px-1.5 py-0.5 text-[10px] font-medium ${cfg.badgeBg}`}>
                    {cfg.label}
                  </span>
                </div>
                {item.description && <p className="text-xs text-custom-text-300 leading-relaxed">{item.description}</p>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
