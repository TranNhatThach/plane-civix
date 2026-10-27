import React, { useEffect, useState } from "react";
import { ArrowUp, Hash, Check, Copy } from "lucide-react";
import type { IDocSection } from "@/data/civix-docs.data";

interface IPlaneChangelogTOCProps {
  releases: IDocSection[];
}

export const PlaneChangelogTOC: React.FC<IPlaneChangelogTOCProps> = ({ releases }) => {
  const [activeId, setActiveId] = useState<string>(releases[0]?.version || "");
  const [copiedLink, setCopiedLink] = useState(false);

  useEffect(() => {
    const scrollContainer = document.getElementById("changelog-scroll-container");
    const target = scrollContainer || window;

    const handleScroll = () => {
      const scrollPos = scrollContainer ? scrollContainer.scrollTop + 140 : window.scrollY + 140;

      for (let i = releases.length - 1; i >= 0; i--) {
        const release = releases[i];
        const targetId = release.version || release.id;
        const el = document.getElementById(targetId);
        if (el) {
          const top = el.offsetTop;
          if (scrollPos >= top) {
            setActiveId(targetId);
            break;
          }
        }
      }
    };

    target.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => target.removeEventListener("scroll", handleScroll);
  }, [releases]);

  const handleScrollTo = (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      history.pushState(null, "", `#${id}`);
      setActiveId(id);
    }
  };

  const handleCopyPageLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2000);
  };

  const scrollToTop = () => {
    const scrollContainer = document.getElementById("changelog-scroll-container");
    if (scrollContainer) {
      scrollContainer.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  return (
    <aside className="sticky top-14 hidden h-[calc(100vh-3.5rem)] w-56 shrink-0 overflow-y-auto px-2 py-6 lg:block">
      <div className="space-y-6">
        <div>
          <h4 className="tracking-wider flex items-center gap-1.5 text-[11px] font-semibold text-tertiary uppercase">
            <Hash className="size-3 text-tertiary" />
            <span>Mục Lục Phiên Bản</span>
          </h4>

          <nav className="relative mt-3 space-y-1">
            {/* Continuous vertical indicator line */}
            <div className="bg-subtle absolute top-2 bottom-2 left-1.5 w-px" />

            {releases.map((release, idx) => {
              const targetId = release.version || release.id;
              const isActive = activeId === targetId;

              return (
                <a
                  key={release.id}
                  href={`#${targetId}`}
                  onClick={(e) => handleScrollTo(e, targetId)}
                  className={`group text-xs relative flex items-start gap-2.5 rounded-md py-1.5 pr-2 pl-4 transition-colors ${
                    isActive ? "font-semibold text-primary" : "text-tertiary hover:text-secondary"
                  }`}
                >
                  {/* Node on vertical line */}
                  <span
                    className={`absolute top-2.5 left-1 size-1.5 -translate-x-1/2 rounded-full transition-all ${
                      isActive
                        ? "ring-accent-primary/20 scale-125 bg-accent-primary ring-2"
                        : "bg-tertiary/60 group-hover:bg-secondary"
                    }`}
                  />

                  <div className="flex flex-col">
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-xs">{release.version}</span>
                      {idx === 0 && (
                        <span className="py-0.2 rounded bg-success-primary/10 px-1 text-[9px] font-semibold text-success-primary">
                          Latest
                        </span>
                      )}
                    </div>
                    <span className="line-clamp-1 text-[11px] text-tertiary group-hover:text-secondary">
                      {release.title}
                    </span>
                  </div>
                </a>
              );
            })}
          </nav>
        </div>

        {/* Quick Utility Links */}
        <div className="space-y-2 border-t border-subtle pt-4">
          <button
            type="button"
            onClick={scrollToTop}
            className="text-xs flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-tertiary transition-colors hover:bg-surface-1 hover:text-primary"
          >
            <ArrowUp className="size-3.5" />
            <span>Trở về đầu trang</span>
          </button>

          <button
            type="button"
            onClick={handleCopyPageLink}
            className="text-xs flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-tertiary transition-colors hover:bg-surface-1 hover:text-primary"
          >
            {copiedLink ? <Check className="size-3.5 text-success-primary" /> : <Copy className="size-3.5" />}
            <span>{copiedLink ? "Đã chép liên kết" : "Chia sẻ changelog"}</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
