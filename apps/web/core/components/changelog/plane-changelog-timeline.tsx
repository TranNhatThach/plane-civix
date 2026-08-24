import React, { useState } from "react";
import { Cloud, Server, Smartphone, Layers, ArrowRight } from "lucide-react";
import type { IReleaseChangelog } from "@/data/civix-changelog.data";

interface IPlaneChangelogTimelineProps {
  releases: IReleaseChangelog[];
  onSelectRelease: (releaseId: string) => void;
}

type TCategoryFilter = "All" | "Cloud" | "Self-hosted" | "Mobile";

export const PlaneChangelogTimeline: React.FC<IPlaneChangelogTimelineProps> = ({ releases, onSelectRelease }) => {
  const [activeCategory, setActiveCategory] = useState<TCategoryFilter>("All");

  const filteredReleases = releases.filter((rel) => {
    if (activeCategory === "All") return true;
    return rel.category === activeCategory;
  });

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-12 sm:px-8">
      {/* Title & Subtitle */}
      <div className="mb-10">
        <h1 className="text-4xl sm:text-5xl text-custom-text-100 mb-3 font-semibold tracking-tight">Changelog</h1>
        <p className="text-base sm:text-lg text-custom-text-300 font-normal">
          New features. Updates. Bug fixes. Enhancements.
        </p>
      </div>

      {/* Filter Tabs (Pill Container) */}
      <div className="mb-14 flex items-center">
        <div className="border-custom-border-200/80 bg-custom-background-90/80 shadow-xs inline-flex items-center gap-1 rounded-xl border p-1 backdrop-blur-sm">
          <button
            type="button"
            onClick={() => setActiveCategory("All")}
            className={`text-xs sm:text-sm inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
              activeCategory === "All"
                ? "bg-custom-background-100 text-custom-text-100 shadow-xs font-semibold"
                : "text-custom-text-300 hover:text-custom-text-100"
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>All</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveCategory("Cloud")}
            className={`text-xs sm:text-sm inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
              activeCategory === "Cloud"
                ? "bg-custom-background-100 text-custom-text-100 shadow-xs font-semibold"
                : "text-custom-text-300 hover:text-custom-text-100"
            }`}
          >
            <Cloud className="h-3.5 w-3.5" />
            <span>Cloud</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveCategory("Self-hosted")}
            className={`text-xs sm:text-sm inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
              activeCategory === "Self-hosted"
                ? "bg-custom-background-100 text-custom-text-100 shadow-xs font-semibold"
                : "text-custom-text-300 hover:text-custom-text-100"
            }`}
          >
            <Server className="h-3.5 w-3.5" />
            <span>Self-hosted</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveCategory("Mobile")}
            className={`text-xs sm:text-sm inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 font-medium transition-all ${
              activeCategory === "Mobile"
                ? "bg-custom-background-100 text-custom-text-100 shadow-xs font-semibold"
                : "text-custom-text-300 hover:text-custom-text-100"
            }`}
          >
            <Smartphone className="h-3.5 w-3.5" />
            <span>Mobile</span>
          </button>
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="space-y-16">
        {filteredReleases.map((release) => (
          <article key={release.id} className="grid grid-cols-1 gap-6 sm:grid-cols-12 sm:gap-10">
            {/* Left Column: Date with blue bullet */}
            <div className="sm:col-span-3">
              <div className="sticky top-24 flex items-center gap-3">
                <div className="h-2.5 w-2.5 shrink-0 rounded-full bg-[#006fee] shadow-[0_0_8px_rgba(0,111,238,0.6)]" />
                <time className="text-sm text-custom-text-200 font-medium">{release.formattedDate}</time>
              </div>
            </div>

            {/* Right Column: Title, Hero Banner Card & Summary */}
            <div className="space-y-4 sm:col-span-9">
              {/* Release Title */}
              <button
                type="button"
                onClick={() => onSelectRelease(release.id)}
                className="text-xl sm:text-2xl text-custom-text-100 hover:text-custom-primary-100 w-full cursor-pointer text-left font-semibold tracking-tight transition-colors"
              >
                {release.title}
              </button>

              {/* Hero Banner Card (Exact style from screenshot) */}
              <button
                type="button"
                onClick={() => onSelectRelease(release.id)}
                className="group border-slate-800/80 shadow-xl hover:border-slate-700 hover:shadow-2xl relative block w-full cursor-pointer overflow-hidden rounded-2xl border bg-gradient-to-br from-[#0c182b] via-[#08101e] to-[#040811] p-8 text-left text-white transition-all duration-300 sm:p-14"
              >
                {/* Ambient Radial Highlights */}
                <div className="bg-blue-500/10 pointer-events-none absolute -top-20 -right-20 h-64 w-64 rounded-full blur-3xl transition-opacity group-hover:opacity-100" />
                <div className="bg-cyan-500/5 pointer-events-none absolute -bottom-20 -left-20 h-64 w-64 rounded-full blur-3xl" />

                {/* Card Content */}
                <div className="relative z-10 flex flex-col items-center text-center">
                  <h3 className="text-xl sm:text-3xl mb-6 max-w-2xl leading-snug font-bold tracking-tight text-white/95 sm:leading-tight">
                    {release.heroBannerTitle || release.title}
                  </h3>

                  {/* Category Pill in Card */}
                  <span className="border-slate-700/60 bg-slate-900/80 text-xs text-slate-300 shadow-inner inline-flex items-center rounded-lg border px-4 py-1.5 font-semibold backdrop-blur-md">
                    Changelog | {release.category}
                  </span>
                </div>

                {/* Card Footer: Plane Logo & Date */}
                <div className="border-slate-800/60 text-xs text-slate-400 relative z-10 mt-12 flex items-center justify-between border-t pt-4 font-medium">
                  <div className="flex items-center gap-2 font-bold text-white/90">
                    <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path d="M3.5 4.5C3.5 3.94772 3.94772 3.5 4.5 3.5H9.5C10.0523 3.5 10.5 3.94772 10.5 4.5V19.5C10.5 20.0523 10.0523 20.5 9.5 20.5H4.5C3.94772 20.5 3.5 20.0523 3.5 19.5V4.5Z" />
                      <path d="M13.5 4.5C13.5 3.94772 13.9477 3.5 14.5 3.5H19.5C20.0523 3.5 20.5 3.94772 20.5 4.5V13.5C20.5 14.0523 20.0523 14.5 19.5 14.5H14.5C13.9477 14.5 13.5 14.0523 13.5 13.5V4.5Z" />
                    </svg>
                    <span>Plane</span>
                  </div>
                  <span>{release.shortDate}</span>
                </div>
              </button>

              {/* Summary Paragraph */}
              <p className="text-sm sm:text-base text-custom-text-200 leading-relaxed">{release.summary}</p>

              {/* View Full Post Link */}
              <button
                type="button"
                onClick={() => onSelectRelease(release.id)}
                className="text-xs sm:text-sm text-custom-primary-100 inline-flex items-center gap-1.5 pt-1 font-semibold hover:underline"
              >
                <span>Read details</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
};
