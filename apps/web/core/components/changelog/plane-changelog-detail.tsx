import React, { useState } from "react";
import {
  ArrowLeft,
  Copy,
  Check,
  Zap,
  Shield,
  Server,
  Bot,
  Code,
  Sparkles,
  Calendar,
  Tag,
  Share2,
  AlertTriangle,
  Lightbulb,
  Info,
} from "lucide-react";
import type { IDocSection, IDocCallout } from "@/data/civix-docs.data";

interface IPlaneChangelogDetailProps {
  release: IDocSection;
  onBack: () => void;
}

const getIconForDoc = (iconName?: string) => {
  switch (iconName) {
    case "zap":
      return <Zap className="text-amber-500 size-5" />;
    case "shield":
      return <Shield className="text-emerald-500 size-5" />;
    case "server":
      return <Server className="text-blue-500 size-5" />;
    case "bot":
      return <Bot className="text-purple-500 size-5" />;
    case "code":
      return <Code className="text-cyan-500 size-5" />;
    default:
      return <Sparkles className="text-blue-500 size-5" />;
  }
};

const CodeSnippet: React.FC<{ code: string }> = ({ code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
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
          <span className="text-[11px]">{copied ? "Đã sao chép" : "Sao chép"}</span>
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
      className={`text-xs sm:text-sm my-4 flex items-start gap-3 rounded-xl border p-4 leading-relaxed ${
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

export const PlaneChangelogDetail: React.FC<IPlaneChangelogDetailProps> = ({ release, onBack }) => {
  const [copiedMd, setCopiedMd] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [activeHeadingIdx, setActiveHeadingIdx] = useState<number>(0);

  const handleCopyMarkdown = () => {
    let md = `# ${release.title}\n\n**Phiên bản:** ${release.version || "N/A"} | **Ngày cập nhật:** ${release.updatedAt || "N/A"}\n\n${release.description}\n\n---\n\n`;

    release.content.forEach((block) => {
      md += `## ${block.heading}\n\n`;
      block.subheadings?.forEach((sub) => {
        md += `### ${sub.title}\n\n`;
        sub.body.forEach((b) => {
          md += `${b}\n\n`;
        });
        if (sub.callout) {
          md += `> [!${sub.callout.type.toUpperCase()}]\n> ${sub.callout.text}\n\n`;
        }
        if (sub.code) {
          md += `\`\`\`bash\n${sub.code}\n\`\`\`\n\n`;
        }
      });
    });

    navigator.clipboard.writeText(md);
    setCopiedMd(true);
    setTimeout(() => setCopiedMd(false), 2000);
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const scrollToHeading = (idx: number, e: React.MouseEvent) => {
    e.preventDefault();
    setActiveHeadingIdx(idx);
    const el = document.getElementById(`heading-${idx}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="relative mx-auto w-full max-w-6xl px-4 py-10 sm:px-8">
      {/* Ambient background glow */}
      <div className="from-blue-500/10 via-indigo-500/5 pointer-events-none absolute top-0 left-1/2 h-80 w-full max-w-4xl -translate-x-1/2 bg-gradient-to-b to-transparent blur-3xl" />

      <div className="relative grid grid-cols-1 gap-12 lg:grid-cols-12">
        {/* Left Sticky Sidebar (Table of Contents & Quick Actions) */}
        <aside className="lg:col-span-3">
          <div className="sticky top-24 space-y-6">
            {/* Back button */}
            <button
              type="button"
              onClick={onBack}
              className="group text-xs text-text-300 hover:text-text-100 inline-flex items-center gap-2 font-semibold transition-colors"
            >
              <ArrowLeft className="size-4 transition-transform group-hover:-translate-x-1" />
              <span>Quay lại danh sách</span>
            </button>

            {/* Release Meta Card */}
            <div className="border-border-200/80 bg-surface-100/70 shadow-xs space-y-3 rounded-xl border p-4 backdrop-blur-sm">
              <div className="flex items-center justify-between">
                <span className="text-xs text-text-100 bg-surface-200 border-border-200 rounded-md border px-2.5 py-0.5 font-bold">
                  {release.version}
                </span>
                <span className="text-xs text-text-400 flex items-center gap-1 font-medium">
                  <Calendar className="size-3" />
                  {release.updatedAt}
                </span>
              </div>
              <div className="text-xs text-text-300 font-medium">
                Mã định danh: <span className="font-mono text-text-200">{release.id}</span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="space-y-2">
              <button
                type="button"
                onClick={handleCopyMarkdown}
                className="border-border-200/80 bg-surface-100/60 hover:bg-surface-200/80 text-xs text-text-200 hover:text-text-100 shadow-xs flex w-full items-center justify-between rounded-xl border px-3.5 py-2 font-medium transition-all"
              >
                <div className="flex items-center gap-2">
                  {copiedMd ? <Check className="text-emerald-500 size-3.5" /> : <Copy className="size-3.5" />}
                  <span>{copiedMd ? "Đã copy Markdown" : "Sao chép Markdown"}</span>
                </div>
              </button>

              <button
                type="button"
                onClick={handleCopyLink}
                className="border-border-200/80 bg-surface-100/60 hover:bg-surface-200/80 text-xs text-text-200 hover:text-text-100 shadow-xs flex w-full items-center justify-between rounded-xl border px-3.5 py-2 font-medium transition-all"
              >
                <div className="flex items-center gap-2">
                  {copiedLink ? <Check className="text-emerald-500 size-3.5" /> : <Share2 className="size-3.5" />}
                  <span>{copiedLink ? "Đã copy liên kết" : "Chia sẻ tài liệu"}</span>
                </div>
              </button>
            </div>

            {/* Table of Contents */}
            <div className="space-y-3 pt-2">
              <h4 className="tracking-wider text-text-400 text-[11px] font-bold uppercase">Mục lục tài liệu</h4>
              <nav className="text-xs space-y-1.5">
                {release.content.map((block, idx) => (
                  <a
                    key={idx}
                    href={`#heading-${idx}`}
                    onClick={(e) => scrollToHeading(idx, e)}
                    className={`block rounded-lg px-2.5 py-1 leading-relaxed transition-colors ${
                      activeHeadingIdx === idx
                        ? "bg-blue-500/10 text-blue-500 border-blue-500 border-l-2 font-semibold"
                        : "text-text-300 hover:text-text-100 hover:bg-surface-200/60"
                    }`}
                  >
                    {block.heading}
                  </a>
                ))}
              </nav>
            </div>
          </div>
        </aside>

        {/* Right Main Content Area */}
        <main className="max-w-3xl space-y-8 lg:col-span-9">
          {/* Header Title Section */}
          <div className="border-border-200/70 space-y-4 border-b pb-8">
            <div className="flex items-center gap-3">
              <div className="bg-surface-200 border-border-200/80 shadow-xs rounded-xl border p-2.5">
                {getIconForDoc(release.iconName)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-blue-500 tracking-wider font-semibold uppercase">
                    {release.version}
                  </span>
                  {release.badge && (
                    <span className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 rounded-full border px-2 py-0.5 text-[10px] font-semibold">
                      {release.badge}
                    </span>
                  )}
                </div>
                <time className="text-xs text-text-400 font-medium">Cập nhật ngày {release.updatedAt}</time>
              </div>
            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold text-text-100 leading-tight tracking-tight">
              {release.title}
            </h1>

            <p className="text-sm sm:text-base text-text-300 font-normal leading-relaxed">{release.description}</p>
          </div>

          {/* Detailed Content Blocks */}
          <div className="space-y-12">
            {release.content.map((block, bIdx) => (
              <section key={bIdx} id={`heading-${bIdx}`} className="scroll-mt-24 space-y-6">
                <h2 className="text-lg sm:text-2xl text-text-100 border-border-200/60 flex items-center gap-2.5 border-b pb-2.5 font-bold tracking-tight">
                  <span className="bg-blue-500 flex size-2 rounded-full" />
                  <span>{block.heading}</span>
                </h2>

                <div className="space-y-8 pl-1">
                  {block.subheadings?.map((sub, sIdx) => (
                    <div key={sIdx} className="space-y-3">
                      <h3 className="text-sm sm:text-base text-text-200 font-bold">{sub.title}</h3>

                      <div className="text-xs sm:text-sm text-text-400 space-y-2 leading-relaxed">
                        {sub.body.map((paragraph, pIdx) => (
                          <p key={pIdx}>{paragraph}</p>
                        ))}
                      </div>

                      {/* Callout box */}
                      {sub.callout && <CalloutBox callout={sub.callout} />}

                      {/* Code snippet */}
                      {sub.code && <CodeSnippet code={sub.code} />}
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>

          {/* Bottom Back Button */}
          <div className="border-border-200/80 mt-16 border-t pt-8">
            <button
              type="button"
              onClick={onBack}
              className="text-xs sm:text-sm border-border-200 bg-surface-100 hover:bg-surface-200 text-text-100 shadow-xs inline-flex items-center gap-2 rounded-xl border px-5 py-2.5 font-semibold transition-all active:scale-95"
            >
              <ArrowLeft className="size-4" />
              <span>Quay lại tất cả bản phát hành</span>
            </button>
          </div>
        </main>
      </div>
    </div>
  );
};
