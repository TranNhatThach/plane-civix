/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState, useMemo, useRef, useEffect } from "react";
import { Search, Sparkles, Bug, Bot, ShieldCheck, Zap, X, Filter } from "lucide-react";
import { CIVIX_CHANGELOG_RELEASES } from "@/data/civix-changelog.data";
import { ChangelogCard } from "./changelog-card";

type FilterTag = "all" | "feature" | "fix" | "agent" | "security" | "improvement";

interface FilterButtonDef {
  id: FilterTag;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const FILTER_BUTTONS: FilterButtonDef[] = [
  { id: "all", label: "Tất cả", icon: Filter },
  { id: "feature", label: "Tính năng mới", icon: Sparkles },
  { id: "fix", label: "Bug Fixes", icon: Bug },
  { id: "agent", label: "AI Agent & Bot", icon: Bot },
  { id: "security", label: "Bảo mật", icon: ShieldCheck },
  { id: "improvement", label: "Cải tiến", icon: Zap },
];

export function CivixChangelogTimeline() {
  const [selectedTag, setSelectedTag] = useState<FilterTag>("all");
  const [searchQuery, setSearchQuery] = useState("");
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Keyboard shortcut (press / or cmd+k to focus search)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        (e.key === "/" || (e.key === "k" && (e.metaKey || e.ctrlKey))) &&
        document.activeElement !== searchInputRef.current
      ) {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Tag item count calculator
  const tagCounts = useMemo(() => {
    const counts: Record<FilterTag, number> = {
      all: CIVIX_CHANGELOG_RELEASES.length,
      feature: 0,
      fix: 0,
      agent: 0,
      security: 0,
      improvement: 0,
    };

    CIVIX_CHANGELOG_RELEASES.forEach((rel) => {
      rel.items.forEach((item) => {
        if (counts[item.type] !== undefined) {
          counts[item.type]++;
        }
      });
    });

    return counts;
  }, []);

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
      {/* Search and Filters Toolbar */}
      <div className="bg-custom-background-100 border-custom-border-200/90 shadow-sm flex flex-col gap-3 rounded-2xl border p-4 sm:p-5">
        {/* Search Input Box */}
        <div className="relative flex-1">
          <Search className="text-custom-text-400 absolute top-1/2 left-3.5 h-4 w-4 -translate-y-1/2" />
          <input
            ref={searchInputRef}
            type="text"
            placeholder="Tìm kiếm tính năng, bug fix, số phiên bản... (nhấn '/' để tìm)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="text-xs sm:text-sm bg-custom-background-90/80 border-custom-border-200 text-custom-text-100 placeholder:text-custom-text-400 focus:border-custom-primary-100 focus:bg-custom-background-100 focus:ring-custom-primary-100/30 w-full rounded-xl border py-2.5 pr-10 pl-10 transition-all focus:ring-1 focus:outline-none"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="text-custom-text-400 hover:text-custom-text-100 absolute top-1/2 right-3 -translate-y-1/2 rounded-full p-1"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {FILTER_BUTTONS.map((btn) => {
            const Icon = btn.icon;
            const isSelected = selectedTag === btn.id;
            const count = tagCounts[btn.id];

            return (
              <button
                key={btn.id}
                type="button"
                onClick={() => setSelectedTag(btn.id)}
                className={`text-xs inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-medium transition-all ${
                  isSelected
                    ? "bg-custom-primary-100 shadow-xs font-semibold text-white"
                    : "bg-custom-background-90 text-custom-text-200 hover:bg-custom-background-80 hover:text-custom-text-100 border-custom-border-200/80 border"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{btn.label}</span>
                {count > 0 && (
                  <span
                    className={`py-0.2 ml-0.5 rounded-full px-1.5 text-[10px] font-bold ${
                      isSelected
                        ? "bg-white/20 text-white"
                        : "bg-custom-background-100 text-custom-text-300 border-custom-border-200 border"
                    }`}
                  >
                    {count}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Release List */}
      {filteredReleases.length === 0 ? (
        <div className="border-custom-border-200 bg-custom-background-100 rounded-2xl border border-dashed py-16 text-center">
          <Bug className="text-custom-text-400 mx-auto mb-3 h-10 w-10 opacity-40" />
          <h3 className="text-sm sm:text-base text-custom-text-100 font-bold">Không tìm thấy bản cập nhật phù hợp</h3>
          <p className="text-xs sm:text-sm text-custom-text-300 mx-auto mt-1 max-w-sm">
            Vui lòng thử tìm kiếm với từ khóa khác hoặc bấm vào bộ lọc &quot;Tất cả&quot;.
          </p>
          <button
            type="button"
            onClick={() => {
              setSelectedTag("all");
              setSearchQuery("");
            }}
            className="text-xs bg-custom-primary-100 shadow-xs mt-4 inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium text-white"
          >
            Đặt lại bộ lọc
          </button>
        </div>
      ) : (
        <div className="flex flex-col">
          {filteredReleases.map((release) => (
            <ChangelogCard key={release.version} release={release} />
          ))}
        </div>
      )}
    </div>
  );
}
