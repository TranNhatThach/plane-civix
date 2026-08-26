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
      return <Zap className="size-5 text-amber-500" />;
    case "shield":
      return <Shield className="size-5 text-emerald-500" />;
    case "server":
      return <Server className="size-5 text-blue-500" />;
    case "bot":
      return <Bot className="size-5 text-purple-500" />;
    case "code":
      return <Code className="size-5 text-cyan-500" />;
    default:
      return <Sparkles className="size-5 text-blue-500" />;
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
          <span className="text-[11px]">{copied ? "Đã sao chép" : "Sao chép"}</span>
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
      className={`my-4 flex items-start gap-3 rounded-xl border p-4 text-xs sm:text-sm leading-relaxed ${
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

  return (
    <div className="relative mx-auto w-full max-w-6xl px-4 py-10 sm:px-8">
      {/* Ambient background glow */}
      <div className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-80 w-full max-w-4xl bg-gradient-to-b from-blue-500/10 via-indigo-500/5 to-transparent blur-3xl" />

      <div className="relative grid grid-cols-1 gap-12 lg:grid-cols-12">
        {/* Left Sticky Sidebar (Table of Contents & Quick Actions) */}
        <aside className="lg:col-span-3">
          <div className="sticky top-24 space-y-6">
            {/* Back button */}
            <button
              type="button"
              onClick={onBack}
              className="group inline-flex items-center gap-2 text-xs font-semibold text-text-300 hover:text-text-100 transition-colors"
            >
              <ArrowLeft className="size-4 transition-transform group-hover:-translate-x-1" />
              <span>Quay lại danh sách</span>
            </button>

            {/* Release Meta Card */}
            <div className="p-4 rounded-xl border border-border-200/80 bg-surface-100/70 backdrop-blur-sm space-y-3 shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-text-100 px-2.5 py-0.5 rounded-md bg-surface-200 border border-border-200">
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
                className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl border border-border-200/80 bg-surface-100/60 hover:bg-surface-200/80 text-xs font-medium text-text-200 hover:text-text-100 transition-all shadow-xs"
              >
                <div className="flex items-center gap-2">
                  {copiedMd ? <Check className="size-3.5 text-emerald-500" /> : <Copy className="size-3.5" />}
                  <span>{copiedMd ? "Đã copy Markdown" : "Sao chép Markdown"}</span>
                </div>
              </button>

              <button
                type="button"
                onClick={handleCopyLink}
                className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl border border-border-200/80 bg-surface-100/60 hover:bg-surface-200/80 text-xs font-medium text-text-200 hover:text-text-100 transition-all shadow-xs"
              >
                <div className="flex items-center gap-2">
                  {copiedLink ? <Check className="size-3.5 text-emerald-500" /> : <Share2 className="size-3.5" />}
                  <span>{copiedLink ? "Đã copy liên kết" : "Chia sẻ tài liệu"}</span>
                </div>
              </button>
            </div>

            {/* Table of Contents */}
            <div className="space-y-3 pt-2">
              <h4 className="text-[11px] font-bold uppercase tracking-wider text-text-400">Mục lục tài liệu</h4>
              <nav className="space-y-1.5 text-xs">
                {release.content.map((block, idx) => (
                  <a
                    key={idx}
                    href={`#heading-${idx}`}
                    onClick={() => setActiveHeadingIdx(idx)}
                    className={`block py-1 px-2.5 rounded-lg transition-colors leading-relaxed ${
                      activeHeadingIdx === idx
                        ? "bg-blue-500/10 text-blue-500 font-semibold border-l-2 border-blue-500"
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
        <main className="max-w-3xl lg:col-span-9 space-y-8">
          {/* Header Title Section */}
          <div className="space-y-4 border-b border-border-200/70 pb-8">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-surface-200 border border-border-200/80 shadow-xs">
                {getIconForDoc(release.iconName)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-blue-500 uppercase tracking-wider">
                    {release.version}
                  </span>
                  {release.badge && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                      {release.badge}
                    </span>
                  )}
                </div>
                <time className="text-xs text-text-400 font-medium">Cập nhật ngày {release.updatedAt}</time>
              </div>
            </div>

            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-text-100 leading-tight">
              {release.title}
            </h1>

            <p className="text-sm sm:text-base text-text-300 leading-relaxed font-normal">{release.description}</p>
          </div>

          {/* Detailed Content Blocks */}
          <div className="space-y-12">
            {release.content.map((block, bIdx) => (
              <section key={bIdx} id={`heading-${bIdx}`} className="scroll-mt-24 space-y-6">
                <h2 className="text-lg sm:text-2xl font-bold tracking-tight text-text-100 border-b border-border-200/60 pb-2.5 flex items-center gap-2.5">
                  <span className="flex size-2 rounded-full bg-blue-500" />
                  <span>{block.heading}</span>
                </h2>

                <div className="space-y-8 pl-1">
                  {block.subheadings?.map((sub, sIdx) => (
                    <div key={sIdx} className="space-y-3">
                      <h3 className="text-sm sm:text-base font-bold text-text-200">{sub.title}</h3>

                      <div className="space-y-2 text-xs sm:text-sm text-text-400 leading-relaxed">
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
          <div className="border-t border-border-200/80 pt-8 mt-16">
            <button
              type="button"
              onClick={onBack}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs sm:text-sm font-semibold rounded-xl border border-border-200 bg-surface-100 hover:bg-surface-200 text-text-100 shadow-xs transition-all active:scale-95"
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
