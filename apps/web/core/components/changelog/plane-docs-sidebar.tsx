import React from "react";
import { Link } from "react-router";
import {
  BookOpen,
  Bot,
  Shield,
  Layers,
  Clock,
  Sparkles,
  GitBranch,
  Terminal,
  Server,
  FileText,
  Compass,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

interface INavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  isActive?: boolean;
  isExternal?: boolean;
}

interface INavSection {
  title: string;
  items: INavItem[];
}

const SIDEBAR_SECTIONS: INavSection[] = [
  {
    title: "Bắt Đầu & Tổng Quan",
    items: [
      {
        title: "Giới thiệu Civix Platform",
        href: "/changelog#overview",
        icon: Compass,
      },
      {
        title: "Kiến trúc hệ thống",
        href: "/changelog#architecture",
        icon: Layers,
      },
    ],
  },
  {
    title: "AI Agent & Bots",
    items: [
      {
        title: "AI Agent Runtime Harness V3",
        href: "/changelog#v1.7.0",
        icon: Bot,
        badge: "V3",
      },
      {
        title: "Slack Socket Mode Bot",
        href: "/changelog#v1.3.5",
        icon: Terminal,
      },
      {
        title: "Telegram 2-Way Sync",
        href: "/changelog#v1.3.0",
        icon: Sparkles,
      },
    ],
  },
  {
    title: "Quản Trị Doanh Nghiệp",
    items: [
      {
        title: "Multi-Tenant & Invite-Only",
        href: "/changelog#v1.6.0",
        icon: Server,
      },
      {
        title: "Sao lưu Workspace độc lập",
        href: "/changelog#v1.6.0",
        icon: Shield,
      },
      {
        title: "Zero-Trust & Phê duyệt HITL",
        href: "/changelog#v1.7.0",
        icon: CheckCircle2,
      },
    ],
  },
  {
    title: "Lịch Sử Phiên Bản",
    items: [
      {
        title: "Changelog (Nhật ký phát hành)",
        href: "/changelog",
        icon: Clock,
        isActive: true,
        badge: "v1.7.0",
      },
      {
        title: "Chuẩn Semantic Versioning",
        href: "/changelog#semver",
        icon: GitBranch,
      },
    ],
  },
  {
    title: "Quy Chuẩn Dự Án",
    items: [
      {
        title: "Cẩm nang phát triển Civix",
        href: "/changelog#standards",
        icon: FileText,
      },
      {
        title: "Quy chuẩn Git & Commits",
        href: "/changelog#git-standards",
        icon: Terminal,
      },
    ],
  },
];

export const PlaneDocsSidebar: React.FC = () => {
  return (
    <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-56 shrink-0 overflow-y-auto border-r border-subtle bg-canvas/40 px-3 py-6 md:block">
      <div className="space-y-6">
        {SIDEBAR_SECTIONS.map((section, idx) => (
          <div key={idx} className="space-y-1.5">
            <h4 className="tracking-wider px-2.5 text-[11px] font-semibold text-tertiary uppercase">{section.title}</h4>
            <div className="space-y-0.5">
              {section.items.map((item, itemIdx) => {
                const Icon = item.icon;
                return (
                  <a
                    key={itemIdx}
                    href={item.href}
                    className={`group text-xs flex items-center justify-between rounded-md px-2.5 py-1.5 font-medium transition-all ${
                      item.isActive
                        ? "bg-surface-2 font-semibold text-primary"
                        : "text-secondary hover:bg-surface-1 hover:text-primary"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Icon
                        className={`size-3.5 shrink-0 transition-colors ${
                          item.isActive ? "text-accent-primary" : "text-tertiary group-hover:text-secondary"
                        }`}
                      />
                      <span className="truncate">{item.title}</span>
                    </div>

                    {item.badge && (
                      <span
                        className={`py-0.2 ml-1.5 shrink-0 rounded px-1.5 text-[10px] font-semibold ${
                          item.isActive ? "bg-accent-primary/10 text-accent-primary" : "bg-surface-2 text-tertiary"
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </a>
                );
              })}
            </div>
          </div>
        ))}

        {/* Civix Engine Status Box */}
        <div className="rounded-lg border border-subtle bg-surface-1/60 p-3">
          <div className="flex items-center gap-2">
            <span className="relative flex size-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success-primary opacity-75" />
              <span className="relative inline-flex size-2 rounded-full bg-success-primary" />
            </span>
            <span className="text-xs font-medium text-primary">Civix Engine Online</span>
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-tertiary">
            Hệ sinh thái Civix được kiểm thử liên tục theo chuẩn CAR-v3 Microkernel.
          </p>
        </div>
      </div>
    </aside>
  );
};
