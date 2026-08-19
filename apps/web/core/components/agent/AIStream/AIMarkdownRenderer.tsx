/* eslint-disable react/no-array-index-key */
/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import React, { useState } from "react";
import { Copy, Check, ExternalLink } from "lucide-react";
import { cn } from "@plane/utils";

interface AIMarkdownRendererProps {
  content: string;
  className?: string;
  isUser?: boolean;
}

const CodeBlock: React.FC<{
  language?: string;
  code: string;
}> = ({ language, code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore clipboard error
    }
  };

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
        <code>{code}</code>
      </pre>
    </div>
  );
};

function renderInline(text: string): React.ReactNode[] {
  // Regex to split on inline code `...`, bold **...**, italic *...*, link [text](url)
  const tokens = text.split(/(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g);

  return tokens.map((tok, idx) => {
    if (!tok) return null;
    if (tok.startsWith("`") && tok.endsWith("`") && tok.length >= 2) {
      return (
        <code
          key={idx}
          className="bg-neutral-800/80 font-mono text-violet-300 border-neutral-700/50 rounded border px-1.5 py-0.5 text-[11px]"
        >
          {tok.slice(1, -1)}
        </code>
      );
    }
    if (tok.startsWith("**") && tok.endsWith("**") && tok.length >= 4) {
      return (
        <strong key={idx} className="font-semibold text-white">
          {tok.slice(2, -2)}
        </strong>
      );
    }
    if (tok.startsWith("*") && tok.endsWith("*") && tok.length >= 2) {
      return (
        <em key={idx} className="text-neutral-300 italic">
          {tok.slice(1, -1)}
        </em>
      );
    }
    const linkMatch = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(tok);
    if (linkMatch) {
      return (
        <a
          key={idx}
          href={linkMatch[2]}
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-0.5 underline underline-offset-2 transition-colors"
        >
          {linkMatch[1]}
          <ExternalLink className="inline-block size-2.5 opacity-70" />
        </a>
      );
    }
    return <span key={idx}>{tok}</span>;
  });
}

function parseBlocks(markdown: string): React.ReactNode[] {
  const lines = markdown.split("\n");
  const nodes: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced Code Block: ```lang
    if (line.trim().startsWith("```")) {
      const language = line.trim().slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      nodes.push(<CodeBlock key={`code-${nodes.length}`} language={language} code={codeLines.join("\n")} />);
      continue;
    }

    // Headings
    if (line.startsWith("# ")) {
      nodes.push(
        <h1
          key={`h1-${nodes.length}`}
          className="text-sm border-neutral-800 mt-3 mb-1.5 border-b pb-1 font-bold tracking-tight text-white"
        >
          {renderInline(line.slice(2))}
        </h1>
      );
      i++;
      continue;
    }
    if (line.startsWith("## ")) {
      nodes.push(
        <h2 key={`h2-${nodes.length}`} className="text-xs mt-2.5 mb-1 font-bold tracking-tight text-white">
          {renderInline(line.slice(3))}
        </h2>
      );
      i++;
      continue;
    }
    if (line.startsWith("### ")) {
      nodes.push(
        <h3 key={`h3-${nodes.length}`} className="text-xs text-neutral-100 mt-2 mb-0.5 font-semibold">
          {renderInline(line.slice(4))}
        </h3>
      );
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith("> ") || line === ">") {
      const quoteLines: string[] = [line.replace(/^>\s?/, "")];
      i++;
      while (i < lines.length && (lines[i].startsWith("> ") || lines[i] === ">")) {
        quoteLines.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      nodes.push(
        <blockquote
          key={`quote-${nodes.length}`}
          className="border-indigo-500 bg-neutral-800/40 text-neutral-300 my-2 rounded-r-md border-l-2 px-3 py-1.5 italic"
        >
          {renderInline(quoteLines.join(" "))}
        </blockquote>
      );
      continue;
    }

    // Markdown Table
    if (line.trim().startsWith("|") && line.trim().endsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }
      if (tableLines.length >= 2) {
        const headerCols = tableLines[0]
          .slice(1, -1)
          .split("|")
          .map((c) => c.trim());
        const bodyLines = tableLines.slice(2); // skip header and delimiter separator row

        nodes.push(
          <div key={`table-${nodes.length}`} className="border-neutral-800 my-2.5 overflow-x-auto rounded-lg border">
            <table className="divide-neutral-800 text-xs min-w-full divide-y text-left">
              <thead className="bg-neutral-800/70 text-neutral-200 font-semibold">
                <tr>
                  {headerCols.map((h, hIdx) => (
                    <th key={hIdx} className="text-xs text-neutral-200 px-3 py-1.5 font-semibold">
                      {renderInline(h)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-neutral-800/60 bg-neutral-900/50 text-neutral-300 divide-y">
                {bodyLines.map((row, rIdx) => {
                  const cols = row
                    .slice(1, -1)
                    .split("|")
                    .map((c) => c.trim());
                  return (
                    <tr key={rIdx} className="hover:bg-neutral-800/30 transition-colors">
                      {cols.map((c, cIdx) => (
                        <td key={cIdx} className="text-xs text-neutral-300 px-3 py-1.5">
                          {renderInline(c)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Unordered List (- , * , • )
    if (/^(\s*[-*•]\s+)/.test(line)) {
      const listItems: string[] = [];
      while (i < lines.length && /^(\s*[-*•]\s+)/.test(lines[i])) {
        listItems.push(lines[i].replace(/^(\s*[-*•]\s+)/, ""));
        i++;
      }
      nodes.push(
        <ul key={`ul-${nodes.length}`} className="text-xs text-neutral-300 my-1.5 ml-4 list-disc space-y-1">
          {listItems.map((item, lIdx) => (
            <li key={lIdx} className="leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered List (1. , 2. )
    if (/^(\s*\d+\.\s+)/.test(line)) {
      const listItems: string[] = [];
      while (i < lines.length && /^(\s*\d+\.\s+)/.test(lines[i])) {
        listItems.push(lines[i].replace(/^(\s*\d+\.\s+)/, ""));
        i++;
      }
      nodes.push(
        <ol key={`ol-${nodes.length}`} className="text-xs text-neutral-300 my-1.5 ml-4 list-decimal space-y-1">
          {listItems.map((item, lIdx) => (
            <li key={lIdx} className="leading-relaxed">
              {renderInline(item)}
            </li>
          ))}
        </ol>
      );
      continue;
    }

    // Empty lines
    if (!line.trim()) {
      i++;
      continue;
    }

    // Normal Paragraph
    nodes.push(
      <p key={`p-${nodes.length}`} className="text-xs text-neutral-200 my-1 leading-relaxed">
        {renderInline(line)}
      </p>
    );
    i++;
  }

  return nodes;
}

export const AIMarkdownRenderer: React.FC<AIMarkdownRendererProps> = ({ content, className, isUser = false }) => {
  if (isUser) {
    return <div className={cn("leading-relaxed whitespace-pre-wrap", className)}>{content}</div>;
  }

  return (
    <div className={cn("prose-invert prose-xs text-neutral-200 max-w-none space-y-2 leading-relaxed prose", className)}>
      {parseBlocks(content)}
    </div>
  );
};
