"use client";

import { useId, type ReactNode } from "react";
import { Card } from "@/components/Card";

type CollapsibleSectionProps = {
  title: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  contentId?: string;
};

export function CollapsibleSection({
  title,
  open,
  onOpenChange,
  children,
  description,
  actions,
  contentId
}: CollapsibleSectionProps) {
  const generatedId = useId();
  const sectionContentId = contentId ?? `collapsible-section-${generatedId}`;

  return (
    <Card className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-ink-900">{title}</h3>
          {description ? <p className="mt-1 text-sm text-ink-500">{description}</p> : null}
        </div>
        <div className="flex items-center gap-2">
          {actions}
          <button
            type="button"
            className="inline-flex items-center justify-center rounded-full border border-blush-200 bg-white px-6 py-3 text-sm font-medium text-blush-700 transition hover:border-blush-300"
            onClick={() => onOpenChange(!open)}
            aria-expanded={open}
            aria-controls={sectionContentId}
          >
            {open ? "Свернуть" : "Добавить"}
          </button>
        </div>
      </div>
      <div
        id={sectionContentId}
        className={`grid overflow-hidden transition-all duration-300 ease-out ${open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"}`}
        aria-hidden={!open}
      >
        <div className="min-h-0">{children}</div>
      </div>
    </Card>
  );
}
