import React, { useState } from "react";
import { ArrowLeft, Copy, Check, ChevronDown, Info, AlertTriangle, Lightbulb } from "lucide-react";
import type { IReleaseChangelog } from "@/data/civix-changelog.data";

interface IPlaneChangelogDetailProps {
  release: IReleaseChangelog;
  onBack: () => void;
}

export const PlaneChangelogDetail: React.FC<IPlaneChangelogDetailProps> = ({ release, onBack }) => {
  const [copied, setCopied] = useState(false);
  const [activeSectionId, setActiveSectionId] = useState<string>(release.sections[0]?.id || "whats-new");

  const handleCopyMarkdown = () => {
    let md = `# ${release.title}\n**Date:** ${release.formattedDate}\n**Category:** ${release.category}\n\n${release.summary}\n\n`;
    release.sections.forEach((sec) => {
      md += `## ${sec.heading}\n\n`;
      sec.items.forEach((item) => {
        md += `### ${item.title}\n\n`;
        item.body.forEach((b) => {
          md += `${b}\n\n`;
        });
        if (item.code) {
          md += "```\n" + item.code + "\n```\n\n";
        }
      });
    });

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleShare = (platform: "twitter" | "linkedin" | "reddit" | "hackernews") => {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(release.title);

    let shareUrl = "";
    if (platform === "twitter") {
      shareUrl = `https://twitter.com/intent/tweet?text=${title}&url=${url}`;
    } else if (platform === "linkedin") {
      shareUrl = `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
    } else if (platform === "reddit") {
      shareUrl = `https://reddit.com/submit?url=${url}&title=${title}`;
    } else if (platform === "hackernews") {
      shareUrl = `https://news.ycombinator.com/submitlink?u=${url}&t=${title}`;
    }
    window.open(shareUrl, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-8">
      <div className="grid grid-cols-1 gap-12 lg:grid-cols-12">
        {/* Left Sticky Sidebar (Exact layout as Screenshot 3) */}
        <aside className="lg:col-span-3">
          <div className="sticky top-24 space-y-8">
            {/* Back button */}
            <button
              type="button"
              onClick={onBack}
              className="group text-sm text-custom-text-200 hover:text-custom-text-100 inline-flex items-center gap-2 font-medium transition-colors"
            >
              <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
              <span>Back to Changelog</span>
            </button>

            {/* Copy as markdown button */}
            <div className="relative">
              <button
                type="button"
                onClick={handleCopyMarkdown}
                className="border-custom-border-200 bg-custom-background-100 text-xs text-custom-text-200 shadow-xs hover:bg-custom-background-90 hover:text-custom-text-100 flex w-full items-center justify-between rounded-lg border px-3.5 py-2 font-medium transition-all"
              >
                <div className="flex items-center gap-2">
                  {copied ? <Check className="text-emerald-500 h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                  <span>{copied ? "Copied to clipboard!" : "Copy as markdown"}</span>
                </div>
                <ChevronDown className="h-3.5 w-3.5 opacity-50" />
              </button>
            </div>

            {/* Table of Contents */}
            <div className="space-y-3">
              <h4 className="text-xs tracking-wider text-custom-text-300 font-bold uppercase">Table of content</h4>
              <nav className="text-xs sm:text-sm space-y-4">
                {release.sections.map((sec) => (
                  <div key={sec.id} className="space-y-2">
                    <a
                      href={`#${sec.id}`}
                      onClick={() => setActiveSectionId(sec.id)}
                      className={`block font-medium transition-colors ${
                        activeSectionId === sec.id
                          ? "font-semibold text-[#006fee]"
                          : "text-custom-text-200 hover:text-custom-text-100"
                      }`}
                    >
                      {sec.heading}
                    </a>

                    {/* Sub-items */}
                    <div className="border-custom-border-200/80 ml-3 space-y-1.5 border-l pl-3">
                      {sec.items.map((item) => (
                        <a
                          key={item.id}
                          href={`#${item.id}`}
                          className="text-xs text-custom-text-300 hover:text-custom-text-100 line-clamp-1 block transition-colors"
                        >
                          {item.title}
                        </a>
                      ))}
                    </div>
                  </div>
                ))}
              </nav>
            </div>

            {/* Share Links */}
            <div className="border-custom-border-200/60 space-y-2.5 border-t pt-4">
              <h4 className="text-xs text-custom-text-300 font-semibold">Share</h4>
              <div className="text-custom-text-300 flex items-center gap-3">
                {/* LinkedIn */}
                <button
                  type="button"
                  onClick={() => handleShare("linkedin")}
                  aria-label="Share on LinkedIn"
                  className="hover:bg-custom-background-90 hover:text-custom-text-100 rounded p-1.5 transition-colors"
                >
                  <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.45 1.45 0 0 0 0-2.9 1.45 1.45 0 0 0 0 2.9m1.4 9.74v-8.37H5.06v8.37z" />
                  </svg>
                </button>

                {/* X / Twitter */}
                <button
                  type="button"
                  onClick={() => handleShare("twitter")}
                  aria-label="Share on X (Twitter)"
                  className="hover:bg-custom-background-90 hover:text-custom-text-100 rounded p-1.5 transition-colors"
                >
                  <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                </button>

                {/* Reddit */}
                <button
                  type="button"
                  onClick={() => handleShare("reddit")}
                  aria-label="Share on Reddit"
                  className="hover:bg-custom-background-90 hover:text-custom-text-100 rounded p-1.5 transition-colors"
                >
                  <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                    <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm5.01 4.744c.688 0 1.25.56 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.11 3.11 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 14c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.56 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z" />
                  </svg>
                </button>

                {/* Hacker News */}
                <button
                  type="button"
                  onClick={() => handleShare("hackernews")}
                  aria-label="Share on Hacker News"
                  className="hover:bg-custom-background-90 hover:text-custom-text-100 rounded p-1.5 transition-colors"
                >
                  <span className="flex h-4 w-4 items-center justify-center rounded-xs bg-[#ff6600] text-[10px] leading-none font-bold text-white">
                    Y
                  </span>
                </button>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Main Content Area (Exact layout from Screenshot 3) */}
        <main className="max-w-3xl lg:col-span-9">
          {/* Category Tag */}
          <div className="mb-2">
            <span className="text-xs tracking-wider font-bold text-[#006fee] uppercase">{release.category}</span>
          </div>

          {/* Post Title */}
          <h1 className="text-3xl sm:text-4xl text-custom-text-100 mb-3 leading-tight font-bold tracking-tight">
            {release.title}
          </h1>

          {/* Date */}
          <time className="text-sm text-custom-text-300 mb-8 block font-medium">{release.shortDate}</time>

          {/* Summary Excerpt */}
          <p className="text-base text-custom-text-200 border-custom-border-200/80 mb-8 border-b pb-6 leading-relaxed">
            {release.summary}
          </p>

          {/* Sections Render */}
          <div className="space-y-12">
            {release.sections.map((section) => (
              <section key={section.id} id={section.id} className="scroll-mt-24 space-y-8">
                <h2 className="text-2xl sm:text-3xl text-custom-text-100 border-custom-border-200/60 border-b pb-3 font-bold tracking-tight">
                  {section.heading}
                </h2>

                <div className="space-y-10">
                  {section.items.map((item) => (
                    <div key={item.id} id={item.id} className="scroll-mt-24 space-y-3.5">
                      <h3 className="text-lg sm:text-xl text-custom-text-100 font-semibold">{item.title}</h3>

                      <div className="text-sm sm:text-base text-custom-text-200 space-y-3 leading-relaxed">
                        {item.body.map((paragraph) => (
                          <p key={`${item.id}-${paragraph.slice(0, 25)}`}>{paragraph}</p>
                        ))}
                      </div>

                      {/* Code Snippet if present */}
                      {item.code && (
                        <div className="border-slate-800 text-slate-100 shadow-md my-4 overflow-hidden rounded-xl border bg-[#0b1324]">
                          <div className="border-slate-800/80 bg-slate-900/60 text-xs font-mono text-slate-400 flex items-center justify-between border-b px-4 py-2">
                            <span>Configuration / Command</span>
                          </div>
                          <pre className="text-xs sm:text-sm font-mono overflow-x-auto p-4">
                            <code>{item.code}</code>
                          </pre>
                        </div>
                      )}

                      {/* Callout box if present */}
                      {item.callout && (
                        <div
                          className={`text-xs sm:text-sm flex items-start gap-3 rounded-xl border p-4 leading-relaxed ${
                            item.callout.type === "warning"
                              ? "border-amber-500/20 bg-amber-500/5 text-amber-600 dark:text-amber-400"
                              : item.callout.type === "tip"
                                ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400"
                                : "border-blue-500/20 bg-blue-500/5 text-blue-600 dark:text-blue-400"
                          }`}
                        >
                          {item.callout.type === "warning" ? (
                            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                          ) : item.callout.type === "tip" ? (
                            <Lightbulb className="mt-0.5 h-4 w-4 shrink-0" />
                          ) : (
                            <Info className="mt-0.5 h-4 w-4 shrink-0" />
                          )}
                          <p>{item.callout.text}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Bottom Back Button */}
          <div className="border-custom-border-200/80 mt-16 border-t pt-8">
            <button
              type="button"
              onClick={onBack}
              className="border-custom-border-200 bg-custom-background-100 text-sm text-custom-text-100 shadow-xs hover:bg-custom-background-90 inline-flex items-center gap-2 rounded-xl border px-5 py-2.5 font-semibold transition-all active:scale-95"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to all release notes</span>
            </button>
          </div>
        </main>
      </div>
    </div>
  );
};
