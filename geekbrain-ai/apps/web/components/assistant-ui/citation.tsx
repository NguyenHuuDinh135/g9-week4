"use client";

import { type FC, type ReactNode, useState } from "react";
import { cn } from "@workspace/ui/lib/utils";

interface CitationBadgeProps {
  type: "KB" | "DB" | "API";
}

const CITATION_CONFIG = {
  KB: {
    label: "KB",
    title: "Knowledge Base",
    description: "Retrieved from company documents (policies, architecture, postmortems)",
    color: "bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800",
    hoverColor: "hover:bg-blue-200 dark:hover:bg-blue-900/50",
  },
  DB: {
    label: "DB",
    title: "Database",
    description: "Queried from historical records (costs, incidents, SLA targets, daily metrics)",
    color: "bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800",
    hoverColor: "hover:bg-emerald-200 dark:hover:bg-emerald-900/50",
  },
  API: {
    label: "API",
    title: "Monitoring API",
    description: "Live system metrics (current status, latency, error rate, requests/min)",
    color: "bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800",
    hoverColor: "hover:bg-amber-200 dark:hover:bg-amber-900/50",
  },
} as const;

export const CitationBadge: FC<CitationBadgeProps> = ({ type }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const config = CITATION_CONFIG[type];

  return (
    <span className="relative inline-block align-baseline">
      <button
        type="button"
        className={cn(
          "inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-semibold leading-none cursor-pointer transition-colors",
          config.color,
          config.hoverColor,
        )}
        onClick={() => setShowTooltip(!showTooltip)}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        aria-label={`Source: ${config.title}`}
      >
        {config.label}
      </button>
      {showTooltip && (
        <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 w-56 rounded-lg border bg-popover p-2.5 text-xs text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 duration-150">
          <span className="font-semibold block mb-0.5">{config.title}</span>
          <span className="text-muted-foreground leading-relaxed">{config.description}</span>
          <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-4 border-transparent border-t-border" />
        </span>
      )}
    </span>
  );
};

const CITATION_REGEX = /\[KB\]|\[DB\]|\[API\]/g;

export function renderWithCitations(text: string): ReactNode[] {
  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const regex = new RegExp(CITATION_REGEX.source, "g");
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const type = match[0].slice(1, -1) as "KB" | "DB" | "API";
    parts.push(<CitationBadge key={`${match.index}-${type}`} type={type} />);
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}
