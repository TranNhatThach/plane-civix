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
      return <Zap className="text-amber-500 size-4" />;
    case "shield":
      return <Shield className="text-emerald-500 size-4" />;
    case "server":
      return <Server className="text-blue-500 size-4" />;
    case "bot":
      return <Bot className="text-purple-500 size-4" />;
    case "code":
      return <Code className="text-cyan-500 size-4" />;
    default:
      return <Sparkles className="text-blue-500 size-4" />;
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
    <div className="border-border-200/80 bg-surface-200/60 relative my-4 overflow-hidden rounded-xl border backdrop-blur-sm">
      <div className="border-border-200/60 bg-surface-200/90 text-xs text-text-400 font-mono flex items-center justify-between border-b px-4 py-2">
        <div className="flex items-center gap-1.5">
          <div className="bg-red-500/80 size-2.5 rounded-full" />
          <div className="bg-amber-500/80 size-2.5 rounded-full" />
          <div className="bg-emerald-500/80 size-2.5 rounded-full" />
          <span className="text-text-400 ml-2 text-[11px]">Terminal / Code</span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="hover:bg-surface-300 text-text-300 hover:text-text-100 inline-flex items-center gap-1 rounded px-2 py-0.5 transition-colors"
        >
          {copied ? <Check className="text-emerald-500 size-3" /> : <Copy className="size-3" />}
          <span className="text-[11px]">{copied ? "Đã copy" : "Sao chép"}</span>
        </button>
      </div>
      <pre className="text-xs font-mono text-text-100 overflow-x-auto p-4 leading-relaxed">
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
      className={`text-xs my-3.5 flex items-start gap-3 rounded-xl border p-3.5 leading-relaxed ${
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
      <div className="from-blue-500/10 via-indigo-500/5 pointer-events-none absolute top-0 left-1/2 h-96 w-full max-w-4xl -translate-x-1/2 bg-gradient-to-b to-transparent blur-3xl" />

      {/* Hero Header */}
      <div className="relative mb-12 text-center sm:text-left">
        <div className="border-border-200/80 bg-surface-100/80 shadow-xs mb-4 inline-flex items-center gap-2 rounded-full border px-3 py-1 backdrop-blur-md">
          <span className="bg-emerald-500 flex size-2 animate-pulse rounded-full" />
          <span className="text-xs text-text-200 font-semibold">Cập nhật liên tục theo chuẩn Civix</span>
          <span className="text-xs text-blue-500 border-border-200/60 border-l pl-1 font-bold">
            {releases[0]?.version || "v1.5.0"}
          </span>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-text-100 mb-3 tracking-tight">
          Nhật ký phát hành & Tính năng
        </h1>
        <p className="text-sm sm:text-base text-text-400 max-w-2xl leading-relaxed">
          Theo dõi toàn bộ các phiên bản nâng cấp tính năng, tối ưu hóa hạ tầng và quy chuẩn kỹ thuật của nền tảng
          Civix.
        </p>

        {/* Search & Tag Filter Bar */}
        <div className="mt-8 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          {/* Search Box */}
          <div className="relative flex-1">
            <Search className="text-text-400 absolute top-1/2 left-3.5 size-4 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm tính năng, mã task, phiên bản..."
              className="text-xs sm:text-sm border-border-200/80 bg-surface-100/70 text-text-100 placeholder:text-text-400 focus:ring-blue-500/20 focus:border-blue-500/50 w-full rounded-xl border py-2 pr-4 pl-10 backdrop-blur-sm transition-all focus:ring-2 focus:outline-none"
            />
          </div>

          {/* Quick Version Filter Pills */}
          <div className="scrollbar-none flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
            {versionTags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => setSelectedTag(tag)}
                className={`text-xs shrink-0 rounded-lg border px-3 py-1.5 font-semibold transition-all ${
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
        <div className="bg-border-200/60 absolute top-6 bottom-6 left-[150px] hidden w-px sm:block" />

        {filteredReleases.length === 0 ? (
          <div className="border-border-200/60 bg-surface-100/40 rounded-2xl border p-8 py-16 text-center">
            <Search className="text-text-400 mx-auto mb-3 size-8 opacity-50" />
            <h3 className="text-sm text-text-100 font-semibold">Không tìm thấy bản phát hành phù hợp</h3>
            <p className="text-xs text-text-400 mt-1">Hãy thử tìm với từ khóa hoặc phiên bản khác.</p>
          </div>
        ) : (
          filteredReleases.map((release, idx) => (
            <article key={release.id} className="group relative grid grid-cols-1 gap-6 sm:grid-cols-12 sm:gap-10">
              {/* Left Column: Version Pill, Date, and Pulse Node */}
              <div className="sm:col-span-3 sm:text-right">
                <div className="flex items-center justify-between gap-2 sm:sticky sm:top-24 sm:flex-col sm:items-end sm:justify-start">
                  {/* Version Pill */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-text-100 bg-surface-200 border-border-200/80 rounded-lg border px-2.5 py-1 font-bold tracking-tight">
                      {release.version || "v1.0.0"}
                    </span>
                    {/* Node on vertical line */}
                    <div className="bg-blue-500 ring-blue-500/20 ring-offset-surface-100 relative -right-[25px] hidden size-2.5 rounded-full ring-4 ring-offset-2 transition-transform group-hover:scale-125 sm:block" />
                  </div>

                  {/* Formatted Date */}
                  <div className="text-xs text-text-400 mt-1 flex items-center gap-1.5 font-medium">
                    <Calendar className="size-3" />
                    <time>{release.updatedAt}</time>
                  </div>

                  {/* Badge */}
                  {release.badge && (
                    <span
                      className={`mt-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${getBadgeColor(
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
                <div className="border-border-200/80 bg-surface-100/60 hover:bg-surface-100/90 shadow-xs hover:shadow-md space-y-6 rounded-2xl border p-6 backdrop-blur-sm transition-all duration-200 sm:p-8">
                  {/* Card Header: Icon + Title */}
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-center gap-2.5">
                        <div className="bg-surface-200/80 border-border-200/60 shadow-xs rounded-xl border p-2">
                          {getIconForDoc(release.iconName)}
                        </div>
                        <span className="text-xs text-text-400 font-semibold tracking-wide uppercase">
                          Release Notes • {release.version}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => onSelectRelease(release.id)}
                        className="text-xs text-blue-500 hover:text-blue-600 inline-flex items-center gap-1 font-semibold transition-all group-hover:translate-x-0.5"
                      >
                        <span>Chi tiết</span>
                        <ArrowRight className="size-3" />
                      </button>
                    </div>

                    <h2
                      onClick={() => onSelectRelease(release.id)}
                      className="text-xl sm:text-2xl text-text-100 hover:text-blue-500 cursor-pointer leading-snug font-bold tracking-tight transition-colors"
                    >
                      {release.title}
                    </h2>

                    <p className="text-xs sm:text-sm text-text-300 leading-relaxed">{release.description}</p>
                  </div>

                  {/* Render Feature Breakdown Headings from civix-docs.json */}
                  <div className="border-border-200/60 space-y-6 border-t pt-5">
                    {release.content.map((block, bIdx) => (
                      <div key={bIdx} className="space-y-3">
                        <h3 className="text-sm sm:text-base text-text-100 flex items-center gap-2 font-bold tracking-tight">
                          <span className="bg-blue-500 flex size-1.5 rounded-full" />
                          <span>{block.heading}</span>
                        </h3>

                        {block.subheadings?.map((sub, sIdx) => (
                          <div key={sIdx} className="border-border-200/80 space-y-2 border-l pl-3.5">
                            <h4 className="text-xs sm:text-sm text-text-200 font-semibold">{sub.title}</h4>

                            <div className="text-xs text-text-400 space-y-1.5 leading-relaxed">
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
                  <div className="border-border-200/60 flex items-center justify-between border-t pt-4">
                    <div className="text-xs text-text-400 flex items-center gap-2">
                      <Tag className="size-3.5" />
                      <span>Civix Core Engine</span>
                    </div>

                    <button
                      type="button"
                      onClick={() => onSelectRelease(release.id)}
                      className="text-xs bg-surface-200 hover:bg-surface-300 text-text-100 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-semibold transition-colors"
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
