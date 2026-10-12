"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const SAFE_PROTOCOLS = new Set(["http:", "https:", "mailto:"]);

function safeUrl(url: string): string {
  try {
    const parsed = new URL(url, "https://example.invalid");
    if (!SAFE_PROTOCOLS.has(parsed.protocol)) return "";
    return url;
  } catch {
    return "";
  }
}

export function Markdown({ children }: { children: string }) {
  return (
    <div className="markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        urlTransform={safeUrl}
        components={{
          a: ({ href, children: linkChildren, ...props }) => (
            <a href={href || undefined} rel="noopener noreferrer nofollow" target="_blank" {...props}>
              {linkChildren}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
