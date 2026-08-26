import React, { useState, useMemo } from "react";
import {
  Search,
  Sparkles,
  ArrowRight,
  Zap,
  Shield,
  Server,
  Bot,
  Code,
  FileText,
  Layers,
  Check,
  Copy,
  Info,
  AlertTriangle,
  Lightbulb,
  Calendar,
  Tag,
} from "lucide-react";
import type { IDocSection, IDocCallout } from "@/data/civix-docs.data";

interface IPlaneChangelogTimelineProps {
  releases: IDocSection[];
  onSelectRelease: (releaseId: string) => void;
}

const getIconForDoc = (iconName?: string) => {
  switch (iconName) {
    case "zap":
      return <Zap className="size-4 text-amber-500" />;
    case "shield":
      return <Shield className="size-4 text-emerald-500" />;
    case "server":
      return <Server className="size-4 text-blue-500" />;
    case "bot":
      return <Bot className="size-4 text-purple-500" />;
    case "code":
      return <Code className="size-4 text-cyan-500" />;
    default:
      return <Sparkles className="size-4 text-blue-500" />;
  }
};

const getBadgeColor = (badge?: string) => {
  if (!badge) return "bg-blue-500/10 text-blue-500 border-blue-500/20";
  if (badge.includes("Mới")) return "bg-emerald-500/10 text-emerald-500 border-emerald-500/20";
  if (badge.includes("Vá Lỗi") || badge.includes("Tối Ưu")) return "bg-blue-500/10 text-blue-500 border-blue-500/20";
  if (badge.includes("Bảo Mật")) return "bg-amber-500/10 text-amber-500 border-amber-500/20";
  return "bg-purple-500/10 text-purple-500 border-purple-500/20";
};

const CodeSnippet: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative my-4 overflow-hidden rounded-xl border border-border-200/80 bg-surface-200/60 backdrop-blur-sm">
      <div className="flex items-center justify-between border-b border-border-200/60 bg-surface-200/90 px-4 py-2 text-xs text-text-400 font-mono">
        <div className="flex items-center gap-1.5">
          <div className="size-2.5 rounded-full bg-red-500/80" />
          <div className="size-2.5 rounded-full bg-amber-500/80" />
          <div className="size-2.5 rounded-full bg-emerald-500/80" />
          <span className="ml-2 text-[11px] text-text-400">Terminal / Code</span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded hover:bg-surface-300 text-text-300 hover:text-text-100 transition-colors"
        >
          {copied ? <Check className="size-3 text-emerald-500" /> : <Copy className="size-3" />}
          <span className="text-[11px]">{copied ? "Đã copy" : "Sao chép"}</span>
        </button>
      </div>
      <pre className="p-4 text-xs font-mono text-text-100 overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
};

const CalloutBox: React.FC<{ callout: IDocCallout }> = ({ callout }) => {
  const isTip = callout.type === "tip";
  const isWarning = callout.type === "warning";

  return (
    <div
      className={`my-3.5 flex items-start gap-3 rounded-xl border p-3.5 text-xs leading-relaxed ${
        isWarning
          ? "border-amber-500/20 bg-amber-500/5 text-amber-600 dark:text-amber-400"
          : isTip
            ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-600 dark:text-emerald-400"
            : "border-blue-500/20 bg-blue-500/5 text-blue-600 dark:text-blue-400"
      }`}
    >
      {isWarning ? (
        <AlertTriangle className="mt-0.5 size-4 shrink-0" />
      ) : isTip ? (
        <Lightbulb className="mt-0.5 size-4 shrink-0" />
      ) : (
        <Info className="mt-0.5 size-4 shrink-0" />
      )}
      <p className="flex-1 font-medium">{callout.text}</p>
    </div>
  );
};

export const PlaneChangelogTimeline: React.FC<IPlaneChangelogTimelineProps> = ({ releases, onSelectRelease }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string>("All");

  // Filter releases by search query & tag
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

  // Extract unique version tags
  const versionTags = useMemo(() => {
    const tags = Array.from(new Set(releases.map((r) => r.version).filter(Boolean))) as string[];
    return ["All", ...tags];
  }, [releases]);

  return (
    <div className="relative mx-auto w-full max-w-5xl px-4 py-12 sm:px-8">
      {/* Ambient Radial Background */}
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-96 w-full max-w-4xl bg-gradient-to-b from-blue-500/10 via-indigo-500/5 to-transparent blur-3xl" />

      {/* Hero Header */}
      <div className="relative mb-12 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 px-3 py-1 mb-4 rounded-full border border-border-200/80 bg-surface-100/80 backdrop-blur-md shadow-xs">
          <span className="flex size-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-semibold text-text-200">Cập nhật liên tục theo chuẩn Civix</span>
          <span className="text-xs font-bold text-blue-500 pl-1 border-l border-border-200/60">
            {releases[0]?.version || "v1.5.0"}
          </span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-text-100 mb-3">
          Nhật ký phát hành & Tính năng
        </h1>
        <p className="text-sm sm:text-base text-text-400 max-w-2xl leading-relaxed">
          Theo dõi toàn bộ các phiên bản nâng cấp tính năng, tối ưu hóa hạ tầng và quy chuẩn kỹ thuật của nền tảng Civix.
        </p>

        {/* Search & Tag Filter Bar */}
        <div className="mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-text-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm tính năng, mã task, phiên bản..."
              className="w-full pl-10 pr-4 py-2 text-xs sm:text-sm rounded-xl border border-border-200/80 bg-surface-100/70 text-text-100 placeholder:text-text-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500/50 backdrop-blur-sm transition-all"
            />
          </div>

          {/* Quick Version Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            {versionTags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => setSelectedTag(tag)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all shrink-0 ${
                  selectedTag === tag
                    ? "bg-text-100 text-surface-100 border-text-100 shadow-xs"
                    : "bg-surface-100/60 text-text-300 border-border-200/60 hover:text-text-100 hover:bg-surface-200/60"
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline Stream */}
      <div className="relative space-y-16">
        {/* Continuous Timeline Connector Line */}
        <div className="hidden sm:block absolute left-[150px] top-6 bottom-6 w-px bg-border-200/60" />

        {filteredReleases.length === 0 ? (
          <div className="text-center py-16 rounded-2xl border border-border-200/60 bg-surface-100/40 p-8">
            <Search className="size-8 text-text-400 mx-auto mb-3 opacity-50" />
            <h3 className="text-sm font-semibold text-text-100">Không tìm thấy bản phát hành phù hợp</h3>
            <p className="text-xs text-text-400 mt-1">Hãy thử tìm với từ khóa hoặc phiên bản khác.</p>
          </div>
        ) : (
          filteredReleases.map((release, idx) => (
            <article key={release.id} className="grid grid-cols-1 sm:grid-cols-12 gap-6 sm:gap-10 relative group">
              {/* Left Column: Version Pill, Date, and Pulse Node */}
              <div className="sm:col-span-3 sm:text-right">
                <div className="sm:sticky sm:top-24 flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2">
                  {/* Version Pill */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold tracking-tight text-text-100 px-2.5 py-1 rounded-lg bg-surface-200 border border-border-200/80">
                      {release.version || "v1.0.0"}
                    </span>
                    {/* Node on vertical line */}
                    <div className="hidden sm:block relative -right-[25px] size-2.5 rounded-full bg-blue-500 ring-4 ring-blue-500/20 ring-offset-2 ring-offset-surface-100 group-hover:scale-125 transition-transform" />
                  </div>

                  {/* Formatted Date */}
                  <div className="flex items-center gap-1.5 text-xs text-text-400 font-medium mt-1">
                    <Calendar className="size-3" />
                    <time>{release.updatedAt}</time>
                  </div>

                  {/* Badge */}
                  {release.badge && (
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border mt-1.5 ${getBadgeColor(
                        release.badge
                      )}`}
                    >
                      {release.badge}
                    </span>
                  )}
                </div>
              </div>

              {/* Right Column: Release Card & Detailed Sections */}
              <div className="sm:col-span-9">
                <div className="rounded-2xl border border-border-200/80 bg-surface-100/60 hover:bg-surface-100/90 backdrop-blur-sm p-6 sm:p-8 shadow-xs hover:shadow-md transition-all duration-200 space-y-6">
                  {/* Card Header: Icon + Title */}
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-2.5">
                        <div className="p-2 rounded-xl bg-surface-200/80 border border-border-200/60 shadow-xs">
                          {getIconForDoc(release.iconName)}
                        </div>
                        <span className="text-xs font-semibold text-text-400 tracking-wide uppercase">
                          Release Notes • {release.version}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => onSelectRelease(release.id)}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-blue-500 hover:text-blue-600 group-hover:translate-x-0.5 transition-all"
                      >
                        <span>Chi tiết</span>
                        <ArrowRight className="size-3" />
                      </button>
                    </div>

                    <h2
                      onClick={() => onSelectRelease(release.id)}
                      className="text-xl sm:text-2xl font-bold tracking-tight text-text-100 hover:text-blue-500 cursor-pointer transition-colors leading-snug"
                    >
                      {release.title}
                    </h2>

                    <p className="text-xs sm:text-sm text-text-300 leading-relaxed">{release.description}</p>
                  </div>

                  {/* Render Feature Breakdown Headings from civix-docs.json */}
                  <div className="border-t border-border-200/60 pt-5 space-y-6">
                    {release.content.map((block, bIdx) => (
                      <div key={bIdx} className="space-y-3">
                        <h3 className="text-sm sm:text-base font-bold text-text-100 tracking-tight flex items-center gap-2">
                          <span className="flex size-1.5 rounded-full bg-blue-500" />
                          <span>{block.heading}</span>
                        </h3>

                        {block.subheadings?.map((sub, sIdx) => (
                          <div key={sIdx} className="pl-3.5 border-l border-border-200/80 space-y-2">
                            <h4 className="text-xs sm:text-sm font-semibold text-text-200">{sub.title}</h4>

                            <div className="space-y-1.5 text-xs text-text-400 leading-relaxed">
                              {sub.body.map((p, pIdx) => (
                                <p key={pIdx}>{p}</p>
                              ))}
                            </div>

                            {/* Callout box */}
                            {sub.callout && <CalloutBox callout={sub.callout} />}

                            {/* Code snippet */}
                            {sub.code && <CodeSnippet code={sub.code} />}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>

                  {/* Card Footer: Action Links */}
                  <div className="border-t border-border-200/60 pt-4 flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-text-400">
                      <Tag className="size-3.5" />
                      <span>Civix Core Engine</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => onSelectRelease(release.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface-200 hover:bg-surface-300 text-text-100 transition-colors"
                    >
                      <span>Xem toàn bộ tài liệu &rarr;</span>
                    </button>
                  </div>
                </div>
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  );
};
