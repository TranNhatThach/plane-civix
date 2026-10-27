import React, { useState, useEffect } from "react";
import { useSearchParams, useLocation } from "react-router";
import {
  PlaneChangelogHeader,
  PlaneDocsSidebar,
  PlaneChangelogTimeline,
  PlaneChangelogTOC,
} from "@/components/changelog";
import { CIVIX_DOCS_SECTIONS } from "@/data/civix-docs.data";

export default function ChangelogPage() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const [searchQuery, setSearchQuery] = useState("");

  // Smooth scroll to target hash on mount / URL change
  useEffect(() => {
    const hash = location.hash.replace("#", "") || searchParams.get("release");
    if (hash) {
      setTimeout(() => {
        const el = document.getElementById(hash);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    }
  }, [location.hash, searchParams]);

  return (
    <div
      id="changelog-scroll-container"
      className="vertical-scrollbar relative flex h-full w-full flex-col overflow-y-auto bg-canvas text-primary selection:bg-accent-primary/20 selection:text-accent-primary"
    >
      {/* Top Navigation Bar */}
      <PlaneChangelogHeader searchQuery={searchQuery} onSearchChange={setSearchQuery} />

      {/* 3-Column Technical Docs Container */}
      <div className="mx-auto flex w-full max-w-7xl flex-1 justify-between px-3 sm:px-6 lg:px-8">
        {/* Left Column: Documentation Navigation */}
        <PlaneDocsSidebar />

        {/* Center Column: Editorial Changelog Stream */}
        <main className="min-w-0 flex-1 px-2 py-8 sm:px-6 lg:px-8">
          <PlaneChangelogTimeline releases={CIVIX_DOCS_SECTIONS} searchQuery={searchQuery} />
        </main>

        {/* Right Column: Sticky Version Table of Contents */}
        <PlaneChangelogTOC releases={CIVIX_DOCS_SECTIONS} />
      </div>

      {/* Minimal Clean Technical Footer */}
      <footer className="text-xs mt-16 border-t border-subtle bg-surface-1/40 py-8 text-tertiary">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <div className="bg-primary text-canvas flex size-4 items-center justify-center rounded">
              <svg className="size-2.5 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.5 4.5C3.5 3.94772 3.94772 3.5 4.5 3.5H9.5C10.0523 3.5 10.5 3.94772 10.5 4.5V19.5C10.5 20.0523 10.0523 20.5 9.5 20.5H4.5C3.94772 20.5 3.5 20.0523 3.5 19.5V4.5Z" />
                <path d="M13.5 4.5C13.5 3.94772 13.9477 3.5 14.5 3.5H19.5C20.0523 3.5 20.5 3.94772 20.5 4.5V13.5C20.5 14.0523 20.0523 14.5 19.5 14.5H14.5C13.9477 14.5 13.5 14.0523 13.5 13.5V4.5Z" />
              </svg>
            </div>
            <span className="font-semibold text-secondary">Civix Documentation Portal</span>
            <span>•</span>
            <span>All rights reserved.</span>
          </div>

          <div className="flex items-center gap-4 text-tertiary">
            <a href="#overview" className="transition-colors hover:text-primary">
              Kiến trúc Civix
            </a>
            <a href="#standards" className="transition-colors hover:text-primary">
              Cẩm nang phát triển
            </a>
            <a href="/changelog" className="transition-colors hover:text-primary">
              Nhật ký phiên bản
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
