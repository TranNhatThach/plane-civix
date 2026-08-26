import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import { PlaneChangelogHeader, PlaneChangelogTimeline, PlaneChangelogDetail } from "@/components/changelog";
import { CIVIX_DOCS_SECTIONS } from "@/data/civix-docs.data";

export default function ChangelogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const releaseParam = searchParams.get("release");

  const [selectedReleaseId, setSelectedReleaseId] = useState<string | null>(releaseParam || null);

  // Sync state with URL parameter
  useEffect(() => {
    if (releaseParam) {
      setSelectedReleaseId(releaseParam);
    } else {
      setSelectedReleaseId(null);
    }
  }, [releaseParam]);

  const handleSelectRelease = (releaseId: string) => {
    setSelectedReleaseId(releaseId);
    setSearchParams({ release: releaseId });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleBackToTimeline = () => {
    setSelectedReleaseId(null);
    setSearchParams({});
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const currentRelease = CIVIX_DOCS_SECTIONS.find((r) => r.id === selectedReleaseId);

  return (
    <div className="relative flex min-h-screen w-full flex-col bg-surface-100/30 text-text-100 selection:bg-blue-500/20 selection:text-blue-500">
      {/* Official Top Navigation Bar */}
      <PlaneChangelogHeader />

      {/* Main Container */}
      <div className="flex-1">
        {selectedReleaseId && currentRelease ? (
          <PlaneChangelogDetail release={currentRelease} onBack={handleBackToTimeline} />
        ) : (
          <PlaneChangelogTimeline releases={CIVIX_DOCS_SECTIONS} onSelectRelease={handleSelectRelease} />
        )}
      </div>

      {/* Minimal Clean Footer */}
      <footer className="border-t border-border-200/60 bg-surface-100/50 py-10 text-xs text-text-400">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 px-4 sm:flex-row">
          <div className="flex items-center gap-2 font-semibold text-text-200">
            <div className="flex h-5 w-5 items-center justify-center rounded bg-gradient-to-tr from-blue-600 to-indigo-500 text-white shadow-xs">
              <svg className="h-3 w-3 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.5 4.5C3.5 3.94772 3.94772 3.5 4.5 3.5H9.5C10.0523 3.5 10.5 3.94772 10.5 4.5V19.5C10.5 20.0523 10.0523 20.5 9.5 20.5H4.5C3.94772 20.5 3.5 20.0523 3.5 19.5V4.5Z" />
                <path d="M13.5 4.5C13.5 3.94772 13.9477 3.5 14.5 3.5H19.5C20.0523 3.5 20.5 3.94772 20.5 4.5V13.5C20.5 14.0523 20.0523 14.5 19.5 14.5H14.5C13.9477 14.5 13.5 14.0523 13.5 13.5V4.5Z" />
              </svg>
            </div>
            <span>Civix Platform Edition</span>
          </div>
          <p>© 2026 Civix Work Management Platform. Đồng bộ dữ liệu tài liệu tự động.</p>
        </div>
      </footer>
    </div>
  );
}
