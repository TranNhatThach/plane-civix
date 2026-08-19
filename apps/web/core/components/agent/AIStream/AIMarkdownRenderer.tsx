/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Copy, Check, ExternalLink } from "lucide-react";
import { cn } from "@plane/utils";

interface AIMarkdownRendererProps {
  content: string;
  className?: string;
  isUser?: boolean;
}

const CodeBlock: React.FC<{
  inline?: boolean;
  className?: string;
  children?: React.ReactNode;
}> = ({ inline, className, children }) => {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || "");
  const language = match ? match[1] : "";
  const codeString = String(children).replace(/\n$/, "");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(codeString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  if (inline) {
    return (
      <code className="bg-neutral-800/80 font-mono text-violet-300 border-neutral-700/50 rounded border px-1.5 py-0.5 text-[11px]">
        {children}
      </code>
    );
  }

  return (
    <div className="border-neutral-800 bg-neutral-950 font-mono text-xs shadow-md relative my-2.5 overflow-hidden rounded-lg border">
      {/* Code Header Bar */}
      <div className="border-neutral-800/80 bg-neutral-900/90 text-neutral-400 flex items-center justify-between border-b px-3 py-1.5 text-[11px]">
        <span className="tracking-wider text-neutral-300 font-semibold uppercase">{language || "code"}</span>
        <button
          type="button"
          onClick={handleCopy}
          className="text-neutral-400 hover:bg-neutral-800 flex items-center gap-1 rounded px-2 py-0.5 transition-colors hover:text-white"
          title="Sao chép mã"
        >
          {copied ? (
            <>
              <Check className="text-emerald-400 size-3" />
              <span className="text-emerald-400 font-medium">Đã chép!</span>
            </>
          ) : (
            <>
              <Copy className="size-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code Content */}
      <pre className="text-neutral-200 overflow-x-auto p-3 text-[12px] leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  );
};

export const AIMarkdownRenderer: React.FC<AIMarkdownRendererProps> = ({ content, className, isUser = false }) => {
  if (isUser) {
    return <div className={cn("leading-relaxed whitespace-pre-wrap", className)}>{content}</div>;
  }

  return (
    <div className={cn("prose-invert prose-xs text-neutral-200 max-w-none space-y-2 leading-relaxed prose", className)}>
      <ReactMarkdown
        components={{
          code: CodeBlock as any,
          h1: ({ children }) => (
            <h1 className="text-sm border-neutral-800 mt-3 mb-1.5 border-b pb-1 font-bold tracking-tight text-white">
              {children}
            </h1>
          ),
          h2: ({ children }) => <h2 className="text-xs mt-2.5 mb-1 font-bold tracking-tight text-white">{children}</h2>,
          h3: ({ children }) => <h3 className="text-xs text-neutral-100 mt-2 mb-0.5 font-semibold">{children}</h3>,
          p: ({ children }) => <p className="text-xs text-neutral-200 my-1 leading-relaxed">{children}</p>,
          ul: ({ children }) => (
            <ul className="text-xs text-neutral-300 my-1.5 ml-4 list-disc space-y-1">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="text-xs text-neutral-300 my-1.5 ml-4 list-decimal space-y-1">{children}</ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className="border-indigo-500 bg-neutral-800/40 text-neutral-300 my-2 rounded-r-md border-l-2 px-3 py-1.5 italic">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="border-neutral-800 my-2.5 overflow-x-auto rounded-lg border">
              <table className="divide-neutral-800 text-xs min-w-full divide-y text-left">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-neutral-800/70 text-neutral-200 font-semibold">{children}</thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-neutral-800/60 bg-neutral-900/50 text-neutral-300 divide-y">{children}</tbody>
          ),
          tr: ({ children }) => <tr className="hover:bg-neutral-800/30 transition-colors">{children}</tr>,
          th: ({ children }) => <th className="text-xs text-neutral-200 px-3 py-1.5 font-semibold">{children}</th>,
          td: ({ children }) => <td className="text-xs text-neutral-300 px-3 py-1.5">{children}</td>,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-0.5 underline underline-offset-2 transition-colors"
            >
              {children}
              <ExternalLink className="inline-block size-2.5 opacity-70" />
            </a>
          ),
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          em: ({ children }) => <em className="text-neutral-300 italic">{children}</em>,
          hr: () => <hr className="border-neutral-800 my-2.5" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
