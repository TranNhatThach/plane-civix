import React from "react";
import { Link } from "react-router";
import { ArrowUpRight, BookOpen, Clock, Layers, Moon, Sun, Search, Sparkles } from "lucide-react";
import { useTheme } from "next-themes";

interface IPlaneChangelogHeaderProps {
  searchQuery?: string;
  onSearchChange?: (val: string) => void;
  onToggleMobileMenu?: () => void;
}

export const PlaneChangelogHeader: React.FC<IPlaneChangelogHeaderProps> = ({
  searchQuery = "",
  onSearchChange,
  onToggleMobileMenu,
}) => {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-subtle bg-canvas/90 backdrop-blur-md transition-colors">
      <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Left: Brand Logo & Navigation */}
        <div className="flex items-center gap-6">
          <Link to="/changelog" className="group flex items-center gap-2.5 transition-opacity">
            {/* Logo Mark */}
            <div className="bg-primary text-canvas flex size-7 items-center justify-center rounded-lg transition-transform group-hover:scale-105">
              <svg className="size-4 fill-current" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M3.5 4.5C3.5 3.94772 3.94772 3.5 4.5 3.5H9.5C10.0523 3.5 10.5 3.94772 10.5 4.5V19.5C10.5 20.0523 10.0523 20.5 9.5 20.5H4.5C3.94772 20.5 3.5 20.0523 3.5 19.5V4.5Z" />
                <path d="M13.5 4.5C13.5 3.94772 13.9477 3.5 14.5 3.5H19.5C20.0523 3.5 20.5 3.94772 20.5 4.5V13.5C20.5 14.0523 20.0523 14.5 19.5 14.5H14.5C13.9477 14.5 13.5 14.0523 13.5 13.5V4.5Z" />
              </svg>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-tight text-primary">Civix Docs</span>
              <span className="rounded-md border border-subtle bg-surface-2 px-1.5 py-0.5 text-[11px] font-medium text-secondary">
                Changelog
              </span>
            </div>
          </Link>

          {/* Desktop Nav Items */}
          <nav className="hidden items-center gap-1 border-l border-subtle pl-4 sm:flex">
            <Link
              to="/changelog"
              className="text-xs inline-flex items-center gap-1.5 rounded-md bg-surface-2 px-2.5 py-1 font-medium text-primary transition-colors"
            >
              <Clock className="size-3.5" />
              <span>Changelog</span>
            </Link>
            <a
              href="#docs"
              className="text-xs inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium text-tertiary transition-colors hover:bg-surface-1 hover:text-primary"
            >
              <BookOpen className="size-3.5" />
              <span>Docs</span>
            </a>
          </nav>
        </div>

        {/* Center: Search Box (Mintlify / Claude Code style) */}
        <div className="relative hidden max-w-sm flex-1 px-4 md:block">
          <div className="relative flex items-center">
            <Search className="pointer-events-none absolute left-3 size-3.5 text-placeholder" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => onSearchChange?.(e.target.value)}
              placeholder="Tìm kiếm tính năng, mã task, phiên bản..."
              className="text-xs focus:border-accent-primary focus:ring-accent-primary w-full rounded-lg border border-subtle bg-surface-1 py-1.5 pr-12 pl-9 text-primary placeholder:text-placeholder focus:ring-1 focus:outline-none"
            />
            <kbd className="pointer-events-none absolute right-2.5 rounded border border-subtle bg-surface-2 px-1.5 py-0.5 text-[10px] font-medium text-tertiary">
              ⌘K
            </kbd>
          </div>
        </div>

        {/* Right: Actions & Theme Switcher */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Switcher */}
          <button
            type="button"
            onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
            aria-label="Toggle theme"
            className="flex size-8 items-center justify-center rounded-lg border border-subtle bg-surface-1 text-secondary transition-colors hover:bg-surface-2 hover:text-primary"
          >
            {resolvedTheme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
          </button>

          {/* Open App / Workspace Button */}
          <Link
            to="/"
            className="text-xs hidden items-center gap-1.5 font-medium text-secondary transition-colors hover:text-primary sm:inline-flex"
          >
            <Layers className="size-3.5" />
            <span>Workspace</span>
          </Link>

          <Link
            to="/"
            className="bg-primary text-xs text-canvas inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-semibold transition-opacity hover:opacity-90 active:scale-95"
          >
            <span>Mở Ứng Dụng</span>
            <ArrowUpRight className="size-3.5" />
          </Link>
        </div>
      </div>
    </header>
  );
};
