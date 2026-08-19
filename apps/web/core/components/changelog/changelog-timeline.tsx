/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState, useMemo } from "react";
import { Search, Filter, Sparkles, Bug, Bot, ShieldCheck, Zap } from "lucide-react";
import { CIVIX_CHANGELOG_RELEASES } from "@/data/civix-changelog.data";
import { ChangelogCard } from "./changelog-card";

type FilterTag = "all" | "feature" | "fix" | "agent" | "security" | "improvement";

const FILTER_BUTTONS: { id: FilterTag; label: string; icon: any }[] = [
  { id: "all", label: "Tất cả", icon: Filter },
  { id: "fix", label: "Bug Fixes", icon: Bug },
  { id: "agent", label: "AI Agent & Bot", icon: Bot },
  { id: "feature", label: "Tính năng mới", icon: Sparkles },
  { id: "security", label: "Bảo mật", icon: ShieldCheck },
  { id: "improvement", label: "Cải tiến", icon: Zap },
];

export function CivixChangelogTimeline() {
  const [selectedTag, setSelectedTag] = useState<FilterTag>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const filteredReleases = useMemo(() => {
    return CIVIX_CHANGELOG_RELEASES.map((release) => {
      let matchedItems = release.items;

      // Filter by tag
      if (selectedTag !== "all") {
        matchedItems = matchedItems.filter((item) => item.type === selectedTag);
      }

      // Filter by search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matchesReleaseMeta =
          release.version.toLowerCase().includes(q) ||
          release.title.toLowerCase().includes(q) ||
          release.summary.toLowerCase().includes(q);

        if (!matchesReleaseMeta) {
          matchedItems = matchedItems.filter(
            (item) =>
              item.title.toLowerCase().includes(q) || (item.description && item.description.toLowerCase().includes(q))
          );
        }
      }

      return Object.assign({}, release, {
        items: matchedItems,
      });
    }).filter((release) => release.items.length > 0 || (selectedTag === "all" && !searchQuery.trim()));
  }, [selectedTag, searchQuery]);

  return (
    <div className="flex w-full flex-col gap-6">
      {/* Search and Filters Bar */}
      <div className="bg-custom-background-90 border-custom-border-200 shadow-xs flex flex-col items-stretch justify-between gap-3 rounded-xl border p-3.5 sm:flex-row sm:items-center">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="text-custom-text-400 absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Tìm kiếm tính năng, bug fix, số phiên bản..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="text-xs bg-custom-background-100 border-custom-border-200 text-custom-text-100 placeholder:text-custom-text-400 focus:border-custom-primary-100 w-full rounded-lg border py-1.5 pr-3 pl-9 focus:outline-none"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5">
          {FILTER_BUTTONS.map((btn) => {
            const Icon = btn.icon;
            const isSelected = selectedTag === btn.id;

            return (
              <button
                key={btn.id}
                type="button"
                onClick={() => setSelectedTag(btn.id)}
                className={`text-xs inline-flex items-center gap-1 rounded-md px-2.5 py-1 font-medium transition-all ${
                  isSelected
                    ? "bg-custom-primary-100 shadow-xs text-white"
                    : "bg-custom-background-100 text-custom-text-200 hover:bg-custom-background-80 border-custom-border-200 border"
                }`}
              >
                <Icon className="h-3 w-3" />
                <span>{btn.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Timeline List */}
      {filteredReleases.length === 0 ? (
        <div className="border-custom-border-200 bg-custom-background-90 rounded-xl border border-dashed py-16 text-center">
          <Bug className="text-custom-text-400 mx-auto mb-2 h-8 w-8 opacity-50" />
          <p className="text-sm text-custom-text-200 font-semibold">Không tìm thấy thay đổi phù hợp</p>
          <p className="text-xs text-custom-text-400 mt-1">
            Vui lòng thử tìm kiếm với từ khóa khác hoặc chọn bộ lọc &quot;Tất cả&quot;.
          </p>
        </div>
      ) : (
        <div className="py-2 pl-2">
          {filteredReleases.map((release) => (
            <ChangelogCard key={release.version} release={release} />
          ))}
        </div>
      )}
    </div>
  );
}
