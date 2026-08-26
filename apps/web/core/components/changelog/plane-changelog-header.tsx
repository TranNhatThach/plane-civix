import React from "react";
import { Link } from "react-router";
import { Sparkles, ArrowUpRight, BookOpen, Clock, Layers } from "lucide-react";

export const PlaneChangelogHeader: React.FC = () => {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border-200/70 bg-surface-100/80 backdrop-blur-xl transition-all">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-8">
        {/* Left: Brand Logo & Civix Badge */}
        <div className="flex items-center gap-6">
          <Link to="/changelog" className="group flex items-center gap-3 transition-opacity">
            {/* Logo Mark */}
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 shadow-md shadow-blue-500/20 text-white">
              <svg className="h-4.5 w-4.5 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.5 4.5C3.5 3.94772 3.94772 3.5 4.5 3.5H9.5C10.0523 3.5 10.5 3.94772 10.5 4.5V19.5C10.5 20.0523 10.0523 20.5 9.5 20.5H4.5C3.94772 20.5 3.5 20.0523 3.5 19.5V4.5Z" />
                <path d="M13.5 4.5C13.5 3.94772 13.9477 3.5 14.5 3.5H19.5C20.0523 3.5 20.5 3.94772 20.5 4.5V13.5C20.5 14.0523 20.0523 14.5 19.5 14.5H14.5C13.9477 14.5 13.5 14.0523 13.5 13.5V4.5Z" />
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-text-100">Civix</span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/20 tracking-wide">
                Changelog
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden items-center gap-1 sm:flex pl-4 border-l border-border-200/60">
            <Link
              to="/changelog"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-surface-200 text-text-100 transition-colors"
            >
              <Clock className="size-3.5" />
              <span>Nhật ký phát hành</span>
            </Link>
            <a
              href="#docs"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg text-text-300 hover:text-text-100 hover:bg-surface-200/60 transition-colors"
            >
              <BookOpen className="size-3.5" />
              <span>Tài liệu kỹ thuật</span>
            </a>
          </nav>
        </div>

        {/* Right CTA Links */}
        <div className="flex items-center gap-3">
          <Link
            to="/"
            className="hidden sm:inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-text-300 hover:text-text-100 transition-colors"
          >
            <Layers className="size-3.5" />
            <span>Không gian làm việc</span>
          </Link>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold rounded-lg bg-text-100 text-surface-100 shadow-sm hover:opacity-90 active:scale-95 transition-all"
          >
            <span>Mở Ứng Dụng</span>
            <ArrowUpRight className="size-3.5" />
          </Link>
        </div>
      </div>
    </header>
  );
};
