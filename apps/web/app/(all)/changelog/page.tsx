import React, { useState } from "react";
import { Link } from "react-router";
import { ArrowLeft, Sparkles, ShieldCheck, BookOpen, History, Bot, Copy, Check, Cpu, Layers } from "lucide-react";
import { CivixChangelogTimeline, CivixDocsSection } from "@/components/changelog";
import { CIVIX_CHANGELOG_RELEASES } from "@/data/civix-changelog.data";
import { CIVIX_DOCS_SECTIONS } from "@/data/civix-docs.data";

export default function ChangelogPage() {
  const [activeTab, setActiveTab] = useState<"changelog" | "docs">("changelog");
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText("/agent có cập nhật gì mới không?");
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  return (
    <div className="bg-custom-background-90 text-custom-text-100 vertical-scrollbar relative flex h-full w-full flex-col overflow-y-auto">
      {/* Top Glassmorphic Navbar */}
      <header className="border-custom-border-200/90 bg-custom-background-100/90 sticky top-0 z-40 flex items-center justify-between border-b px-4 py-3 backdrop-blur-md sm:px-8">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="text-xs text-custom-text-200 hover:text-custom-text-100 hover:bg-custom-background-90 border-custom-border-200 shadow-xs inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 font-medium transition-all"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Quay lại ứng dụng</span>
            <span className="sm:hidden">Quay lại</span>
          </Link>

          <div className="bg-custom-border-200 hidden h-4 w-[1px] sm:block" />

          {/* Brand */}
          <div className="flex items-center gap-2.5">
            <div className="bg-custom-primary-100 text-xs shadow-xs flex h-7 w-7 items-center justify-center rounded-lg font-bold text-white">
              C
            </div>
            <div className="flex flex-col">
              <span className="text-sm text-custom-text-100 font-extrabold leading-none tracking-tight">Civix Hub</span>
              <span className="text-custom-text-300 text-[10px] font-medium">Docs & Changelog</span>
            </div>
          </div>
        </div>

        {/* Tab Switcher in Navbar */}
        <div className="bg-custom-background-90 border-custom-border-200 flex items-center rounded-xl border p-1">
          <button
            type="button"
            onClick={() => setActiveTab("changelog")}
            className={`text-xs inline-flex items-center gap-1.5 rounded-lg px-3 py-1 font-medium transition-all ${
              activeTab === "changelog"
                ? "bg-custom-background-100 text-custom-primary-100 shadow-xs font-semibold"
                : "text-custom-text-200 hover:text-custom-text-100"
            }`}
          >
            <History className="h-3.5 w-3.5" />
            <span>Changelog</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("docs")}
            className={`text-xs inline-flex items-center gap-1.5 rounded-lg px-3 py-1 font-medium transition-all ${
              activeTab === "docs"
                ? "bg-custom-background-100 text-custom-primary-100 shadow-xs font-semibold"
                : "text-custom-text-200 hover:text-custom-text-100"
            }`}
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Documentation</span>
          </button>
        </div>

        {/* Version Badge */}
        <div className="hidden items-center gap-2 md:flex">
          <span className="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 text-xs inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-medium">
            <span className="bg-emerald-500 h-1.5 w-1.5 animate-pulse rounded-full" />
            v1.4.1 Sẵn sàng
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-8 px-4 py-8 sm:px-6 md:py-10">
        {/* Hero Section */}
        <div className="border-custom-border-200/80 bg-custom-background-100 shadow-xs relative overflow-hidden rounded-3xl border p-6 sm:p-10">
          {/* Subtle Ambient Radial Glow */}
          <div className="bg-custom-primary-100/10 pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full blur-3xl" />
          <div className="bg-emerald-500/5 pointer-events-none absolute -bottom-24 -left-24 h-80 w-80 rounded-full blur-3xl" />

          <div className="relative z-10 max-w-3xl">
            <div className="text-xs bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 mb-3.5 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-semibold">
              <Sparkles className="h-3.5 w-3.5" />
              Civix Engineering & Release Portal
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-custom-text-100 mb-3 tracking-tight">
              {activeTab === "changelog" ? "Nhật Ký Cập Nhật Phiên Bản" : "Tài Liệu Kỹ Thuật & Cẩm Nang Quy Chuẩn"}
            </h1>
            <p className="text-xs sm:text-base text-custom-text-200 mb-6 leading-relaxed">
              {activeTab === "changelog"
                ? "Theo dõi chi tiết các tính năng mới, bản vá lỗi (bug fixes), cải tiến hiệu năng và các thay đổi kiến trúc qua từng phiên bản của hệ thống Plane-Civix."
                : "Hướng dẫn tương tác với AI Agent qua Slack/Telegram, quy chuẩn văn hóa công sở, quy chuẩn viết tài liệu 5 phần và quy trình phát hành SemVer."}
            </p>

            {/* Quick Metrics Pills */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <div className="bg-custom-background-90 border-custom-border-200 text-xs text-custom-text-200 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1">
                <Layers className="text-custom-primary-100 h-3.5 w-3.5" />
                <span>5 Phiên bản phát hành</span>
              </div>
              <div className="bg-custom-background-90 border-custom-border-200 text-xs text-custom-text-200 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1">
                <Bot className="text-blue-500 h-3.5 w-3.5" />
                <span>Slack AI Agent Socket Mode</span>
              </div>
              <div className="bg-custom-background-90 border-custom-border-200 text-xs text-custom-text-200 inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1">
                <ShieldCheck className="text-emerald-500 h-3.5 w-3.5" />
                <span>Phân lập Workspace an toàn</span>
              </div>
            </div>
          </div>
        </div>

        {/* 2-Column Responsive Layout */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* Main Feed Column */}
          <div className="lg:col-span-8">
            {activeTab === "changelog" ? <CivixChangelogTimeline /> : <CivixDocsSection />}
          </div>

          {/* Sticky Desktop Sidebar */}
          <aside className="space-y-6 lg:col-span-4">
            {/* Version Quick Jump (when on Changelog tab) */}
            {activeTab === "changelog" && (
              <div className="border-custom-border-200 bg-custom-background-100 shadow-sm sticky top-20 rounded-2xl border p-5">
                <div className="text-xs text-custom-text-300 tracking-wider mb-3 flex items-center justify-between font-bold uppercase">
                  <span>Mục lục phiên bản</span>
                  <History className="h-3.5 w-3.5" />
                </div>
                <div className="space-y-1.5">
                  {CIVIX_CHANGELOG_RELEASES.map((rel) => {
                    const anchor = `#release-${rel.version.replace(/\./g, "-")}`;
                    return (
                      <a
                        key={rel.version}
                        href={anchor}
                        className="group text-xs text-custom-text-200 hover:text-custom-text-100 hover:bg-custom-background-90 flex items-center justify-between rounded-lg p-2 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <span className="group-hover:text-custom-primary-100 font-semibold">{rel.version}</span>
                          <span className="text-custom-text-300 line-clamp-1 max-w-[140px] text-[11px]">
                            {rel.title}
                          </span>
                        </div>
                        <span className="text-custom-text-300 text-[10px]">{rel.releaseDate}</span>
                      </a>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Quick Docs Index (when on Docs tab) */}
            {activeTab === "docs" && (
              <div className="border-custom-border-200 bg-custom-background-100 shadow-sm sticky top-20 rounded-2xl border p-5">
                <div className="text-xs text-custom-text-300 tracking-wider mb-3 flex items-center justify-between font-bold uppercase">
                  <span>Mục lục tài liệu</span>
                  <BookOpen className="h-3.5 w-3.5" />
                </div>
                <div className="space-y-1.5">
                  {CIVIX_DOCS_SECTIONS.map((sec) => (
                    <a
                      key={sec.id}
                      href={`#${sec.id}`}
                      className="group text-xs text-custom-text-200 hover:text-custom-text-100 hover:bg-custom-background-90 flex items-center justify-between rounded-lg p-2 transition-colors"
                    >
                      <div className="flex min-w-0 items-center gap-2 pr-2">
                        {sec.version && (
                          <span className="text-custom-primary-100 bg-custom-primary-100/10 border-custom-primary-100/20 shrink-0 rounded border px-1.5 py-0.5 text-[10px] font-bold">
                            {sec.version}
                          </span>
                        )}
                        <span className="group-hover:text-custom-primary-100 truncate font-medium">{sec.title}</span>
                      </div>
                      <span className="text-custom-text-300 shrink-0 text-[10px]">{sec.updatedAt}</span>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Slack AI Bot Interactive Card */}
            <div className="border-custom-border-200 bg-custom-background-100 shadow-sm rounded-2xl border p-5">
              <div className="mb-2.5 flex items-center gap-2.5">
                <div className="bg-blue-500/10 text-blue-500 border-blue-500/20 flex h-8 w-8 items-center justify-center rounded-lg border">
                  <Bot className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-xs text-custom-text-100 font-bold">Tra cứu nhanh trên Slack</h3>
                  <p className="text-custom-text-300 text-[11px]">Gõ /agent để tra cứu bản cập nhật</p>
                </div>
              </div>
              <p className="text-xs text-custom-text-200 mb-3 leading-relaxed">
                Bạn có thể hỏi trực tiếp Slack AI Bot để xem danh sách lỗi đã fix hoặc tóm tắt các tính năng mới mà
                không cần mở trình duyệt.
              </p>
              <div className="bg-custom-background-90 border-custom-border-200 flex items-center justify-between rounded-lg border px-3 py-2">
                <code className="text-xs font-mono text-custom-primary-100">/agent có cập nhật gì mới không?</code>
                <button
                  type="button"
                  onClick={handleCopyPrompt}
                  title="Sao chép lệnh"
                  className="text-custom-text-300 hover:text-custom-text-100 ml-2 rounded p-1"
                >
                  {copiedPrompt ? <Check className="text-emerald-500 h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                </button>
              </div>
            </div>

            {/* Platform Specs */}
            <div className="border-custom-border-200 bg-custom-background-100 shadow-sm text-xs text-custom-text-300 space-y-2 rounded-2xl border p-5">
              <div className="text-custom-text-100 tracking-wider mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase">
                <Cpu className="text-custom-primary-100 h-3.5 w-3.5" />
                Nền tảng kỹ thuật
              </div>
              <div className="border-custom-border-200/50 flex items-center justify-between border-b pb-1.5">
                <span>Backend Framework</span>
                <span className="font-mono text-custom-text-100 font-medium">Django 5.2 LTS</span>
              </div>
              <div className="border-custom-border-200/50 flex items-center justify-between border-b pb-1.5">
                <span>Frontend Router</span>
                <span className="font-mono text-custom-text-100 font-medium">React Router v7 Vite</span>
              </div>
              <div className="border-custom-border-200/50 flex items-center justify-between border-b pb-1.5">
                <span>Cơ sở dữ liệu</span>
                <span className="font-mono text-custom-text-100 font-medium">PostgreSQL 16</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Chế độ sao lưu</span>
                <span className="font-mono text-emerald-500 font-medium">Tự động 5 phút</span>
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-custom-border-200/80 bg-custom-background-100 mt-12 border-t px-6 py-8 text-center">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <span className="bg-custom-primary-100 text-xs flex h-6 w-6 items-center justify-center rounded-md font-bold text-white">
              C
            </span>
            <span className="text-xs text-custom-text-100 font-bold">Civix Project Management Platform</span>
          </div>
          <p className="text-xs text-custom-text-300">© 2026 Civix Core Engineering Team. Bản quyền thuộc về Civix.</p>
        </div>
      </footer>
    </div>
  );
}
