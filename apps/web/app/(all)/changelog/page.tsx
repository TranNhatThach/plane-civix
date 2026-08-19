import React from "react";
import { Link } from "react-router";
import { ArrowLeft, Sparkles, ShieldCheck } from "lucide-react";
import { CivixChangelogTimeline } from "@/components/changelog";

export default function ChangelogPage() {
  return (
    <div className="bg-custom-background-100 text-custom-text-100 flex min-h-screen flex-col">
      {/* Top Navbar */}
      <header className="border-custom-border-200 bg-custom-background-100/80 sticky top-0 z-30 flex items-center justify-between border-b px-6 py-3.5 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="text-xs text-custom-text-200 hover:text-custom-text-100 hover:bg-custom-background-90 border-custom-border-200 inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 font-medium transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Quay lại ứng dụng</span>
          </Link>
          <div className="bg-custom-border-200 mx-1 h-4 w-[1px]" />
          <div className="flex items-center gap-2">
            <span className="bg-custom-primary-100 text-xs flex h-6 w-6 items-center justify-center rounded-md font-bold text-white">
              C
            </span>
            <span className="text-sm text-custom-text-100 font-bold tracking-tight">Civix Docs & Changelog</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium">
            <ShieldCheck className="h-3 w-3" />
            Bảo mật nội bộ
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-8 px-4 py-8 sm:px-6 md:py-12">
        {/* Hero Section */}
        <div className="border-custom-border-200 border-b pb-8 text-center sm:text-left">
          <div className="text-xs bg-custom-primary-100/10 text-custom-primary-100 border-custom-primary-100/20 mb-3 inline-flex items-center gap-1.5 rounded-full border px-3 py-1 font-semibold">
            <Sparkles className="h-3.5 w-3.5" />
            Nhật Ký Phát Triển & Cập Nhật Tính Năng
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-custom-text-100 mb-2 tracking-tight">
            Civix Release Notes & Changelog
          </h1>
          <p className="text-sm text-custom-text-200 max-w-2xl leading-relaxed">
            Theo dõi chi tiết các tính năng mới, các cải tiến hiệu năng và danh sách các lỗi (bugs) đã được khắc phục
            qua từng phiên bản phát hành của hệ thống Plane-Civix.
          </p>
        </div>

        {/* Timeline Component */}
        <CivixChangelogTimeline />
      </main>

      {/* Footer */}
      <footer className="border-custom-border-200 text-xs text-custom-text-300 border-t px-6 py-6 text-center">
        <p>© 2026 Civix Project Management Platform. Được phát triển và bảo trì bởi Civix Core Engineering Team.</p>
      </footer>
    </div>
  );
}
