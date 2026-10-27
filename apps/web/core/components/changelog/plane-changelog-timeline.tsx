import React, { useState, useMemo } from "react";
import {
  Link as LinkIcon,
  Check,
  Copy,
  Info,
  AlertTriangle,
  Lightbulb,
  Sparkles,
  Terminal,
  Shield,
  Bot,
  Server,
  Code,
  Calendar,
  Search,
  Filter,
} from "lucide-react";
import type { IDocSection, IDocCallout } from "@/data/civix-docs.data";

interface IPlaneChangelogTimelineProps {
  releases: IDocSection[];
  searchQuery?: string;
  onSelectRelease?: (releaseId: string) => void;
}

const getBadgeStyle = (badge?: string) => {
  if (!badge) return "bg-surface-2 text-secondary border-subtle";
  if (badge.includes("Mới")) return "bg-success-primary/10 text-success-primary border-success-primary/20";
  if (badge.includes("Ổn định")) return "bg-accent-primary/10 text-accent-primary border-accent-primary/20";
  if (badge.includes("Bảo Mật")) return "bg-warning-primary/10 text-warning-primary border-warning-primary/20";
  return "bg-surface-2 text-secondary border-subtle";
};

const MinimalCodeBlock: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="group relative my-3.5 overflow-hidden rounded-lg border border-subtle bg-surface-1">
      <div className="flex items-center justify-between border-b border-subtle bg-surface-2/60 px-3.5 py-1.5 text-[11px] text-tertiary">
        <span className="font-mono font-medium text-secondary">terminal</span>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-tertiary transition-colors hover:bg-surface-2 hover:text-primary"
        >
          {copied ? <Check className="size-3 text-success-primary" /> : <Copy className="size-3" />}
          <span>{copied ? "Đã chép" : "Sao chép"}</span>
        </button>
      </div>
      <pre className="font-mono text-xs overflow-x-auto p-3.5 leading-relaxed text-primary">
        <code>{code}</code>
      </pre>
    </div>
  );
};

const AdmonitionCallout: React.FC<{ callout: IDocCallout }> = ({ callout }) => {
  const isWarning = callout.type === "warning";
  const isTip = callout.type === "tip";

  return (
    <div
      className={`text-xs my-3.5 flex items-start gap-3 rounded-r-lg border-l-2 p-3 leading-relaxed transition-colors ${
        isWarning
          ? "border-warning-primary bg-warning-primary/5 text-warning-primary"
          : isTip
            ? "border-success-primary bg-success-primary/5 text-success-primary"
            : "border-accent-primary bg-accent-primary/5 text-accent-primary"
      }`}
    >
      <div className="mt-0.5 shrink-0">
        {isWarning ? (
          <AlertTriangle className="size-4" />
        ) : isTip ? (
          <Lightbulb className="size-4" />
        ) : (
          <Info className="size-4" />
        )}
      </div>
      <div className="text-secondary">
        <p className="font-medium text-primary">{callout.text}</p>
      </div>
    </div>
  );
};

export const PlaneChangelogTimeline: React.FC<IPlaneChangelogTimelineProps> = ({ releases, searchQuery = "" }) => {
  const [selectedTag, setSelectedTag] = useState<string>("All");
  const [copiedAnchorId, setCopiedAnchorId] = useState<string | null>(null);

  // Extract unique version numbers
  const versionTags = useMemo(() => {
    const tags = Array.from(new Set(releases.map((r) => r.version).filter(Boolean))) as string[];
    return ["All", ...tags];
  }, [releases]);

  // Filter releases
  const filteredReleases = useMemo(() => {
    return releases.filter((release) => {
      const matchesTag = selectedTag === "All" || release.version === selectedTag;
      if (!matchesTag) return false;

      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const matchTitle = release.title.toLowerCase().includes(q);
      const matchDesc = release.description.toLowerCase().includes(q);
      const matchVersion = release.version?.toLowerCase().includes(q);
      const matchContent = release.content.some(
        (c) =>
          c.heading.toLowerCase().includes(q) ||
          c.subheadings?.some(
            (s) => s.title.toLowerCase().includes(q) || s.body.some((b) => b.toLowerCase().includes(q))
          )
      );
      return matchTitle || matchDesc || matchVersion || matchContent;
    });
  }, [releases, searchQuery, selectedTag]);

  const handleCopyAnchor = (id: string) => {
    const url = `${window.location.origin}${window.location.pathname}#${id}`;
    navigator.clipboard.writeText(url);
    setCopiedAnchorId(id);
    setTimeout(() => setCopiedAnchorId(null), 2000);
  };

  return (
    <div className="w-full max-w-3xl space-y-12 py-2">
      {/* Editorial Header Section (Mintlify / Claude Code Docs style) */}
      <div className="border-b border-subtle pb-8">
        {/* Breadcrumb */}
        <div className="text-xs mb-3 flex items-center gap-1.5 text-tertiary">
          <span>Documentation</span>
          <span>/</span>
          <span>Getting Started</span>
          <span>/</span>
          <span className="font-medium text-primary">Changelog</span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-primary">Civix Platform changelog</h1>

        <p className="text-sm sm:text-base mt-3 leading-relaxed text-secondary">
          Nhật ký phát hành chính thức của Plane-Civix. Cập nhật chi tiết các tính năng mới, nâng cấp kiến trúc vi nhân
          AI Agent Runtime Harness, mô hình Multi-tenant phân lập và các bản vá lỗi theo từng phiên bản.
        </p>

        <div className="text-xs mt-4 flex flex-wrap items-center gap-2 text-tertiary">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-subtle bg-surface-1 px-2.5 py-1">
            <span className="size-2 rounded-full bg-success-primary" />
            <span className="font-medium text-secondary">Phiên bản hiện tại:</span>
            <span className="font-mono font-semibold text-primary">{releases[0]?.version || "v1.7.0"}</span>
          </div>
          <span>•</span>
          <span>
            Đồng bộ tự động từ <code className="font-mono text-secondary">civix-docs.json</code>
          </span>
        </div>

        {/* Quick Version Filter Pills */}
        <div className="text-xs mt-6 flex items-center gap-1.5 overflow-x-auto pb-1">
          <span className="mr-1 font-medium text-tertiary">Lọc theo:</span>
          {versionTags.slice(0, 8).map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => setSelectedTag(tag)}
              className={`font-mono shrink-0 rounded-md border px-2.5 py-1 transition-colors ${
                selectedTag === tag
                  ? "border-accent-primary bg-accent-primary text-white"
                  : "border-subtle bg-surface-1 text-secondary hover:bg-surface-2 hover:text-primary"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Release Stream (Continuous Chronological Layout) */}
      <div className="space-y-16">
        {filteredReleases.length === 0 ? (
          <div className="rounded-xl border border-subtle bg-surface-1/50 p-12 text-center">
            <Search className="mx-auto mb-3 size-6 text-tertiary opacity-60" />
            <h3 className="text-sm font-semibold text-primary">Không tìm thấy bản phát hành phù hợp</h3>
            <p className="text-xs mt-1 text-tertiary">Vui lòng thử tìm kiếm với từ khóa hoặc phiên bản khác.</p>
          </div>
        ) : (
          filteredReleases.map((release, idx) => {
            const anchorId = release.version || release.id;
            const isCopied = copiedAnchorId === anchorId;

            return (
              <article
                key={release.id}
                id={anchorId}
                className="scroll-mt-24 space-y-6 border-b border-subtle pb-14 last:border-b-0"
              >
                {/* Version Heading & Metadata */}
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5">
                      <h2 className="group text-2xl flex items-center gap-2 font-bold tracking-tight text-primary">
                        <span className="font-mono">{release.version || "v1.0.0"}</span>
                        <button
                          type="button"
                          onClick={() => handleCopyAnchor(anchorId)}
                          title="Sao chép liên kết phiên bản"
                          className="opacity-0 transition-opacity group-hover:opacity-100 hover:text-accent-primary"
                        >
                          {isCopied ? (
                            <Check className="size-4 text-success-primary" />
                          ) : (
                            <LinkIcon className="size-4 text-tertiary" />
                          )}
                        </button>
                      </h2>

                      {release.badge && (
                        <span
                          className={`rounded-full border px-2 py-0.5 text-[11px] font-medium ${getBadgeStyle(
                            release.badge
                          )}`}
                        >
                          {release.badge}
                        </span>
                      )}
                    </div>

                    {/* Release Date */}
                    {release.updatedAt && (
                      <div className="text-xs flex items-center gap-1.5 text-tertiary">
                        <Calendar className="size-3.5" />
                        <time>{release.updatedAt}</time>
                      </div>
                    )}
                  </div>

                  {/* Release Milestone Title */}
                  <h3 className="text-base sm:text-lg leading-snug font-semibold text-primary">{release.title}</h3>

                  {/* Summary / Description */}
                  <p className="text-xs sm:text-sm leading-relaxed text-secondary">{release.description}</p>
                </div>

                {/* Structured Changes & Breakdown */}
                <div className="space-y-6 pt-2">
                  {release.content.map((block, bIdx) => (
                    <div key={bIdx} className="space-y-3">
                      <h4 className="text-sm flex items-center gap-2 font-semibold tracking-tight text-primary">
                        <span className="size-1.5 rounded-full bg-accent-primary" />
                        <span>{block.heading}</span>
                      </h4>

                      {block.subheadings?.map((sub, sIdx) => (
                        <div key={sIdx} className="ml-3 space-y-2 border-l border-subtle pl-4">
                          <h5 className="text-xs sm:text-sm font-semibold text-secondary">{sub.title}</h5>

                          <div className="text-xs space-y-1.5 leading-relaxed text-tertiary">
                            {sub.body.map((paragraph, pIdx) => (
                              <p key={pIdx}>{paragraph}</p>
                            ))}
                          </div>

                          {/* Admonition Callout */}
                          {sub.callout && <AdmonitionCallout callout={sub.callout} />}

                          {/* Code Snippet */}
                          {sub.code && <MinimalCodeBlock code={sub.code} />}
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              </article>
            );
          })
        )}
      </div>
    </div>
  );
};
