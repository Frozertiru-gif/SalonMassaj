"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/Button";
import type { WeeklyRitual } from "@/lib/types";

type WeeklyRitualCarouselProps = {
  rituals: WeeklyRitual[];
  intervalMs?: number;
};

export function WeeklyRitualCarousel({ rituals, intervalMs = 5000 }: WeeklyRitualCarouselProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const items = useMemo(() => rituals.filter((ritual) => ritual.is_active), [rituals]);

  useEffect(() => {
    if (items.length <= 1) {
      return;
    }
    const timer = setInterval(() => {
      setActiveIndex((current) => (current + 1) % items.length);
    }, intervalMs);
    return () => clearInterval(timer);
  }, [items.length, intervalMs]);

  useEffect(() => {
    if (activeIndex >= items.length) {
      setActiveIndex(0);
    }
  }, [activeIndex, items.length]);

  if (items.length === 0) {
    return null;
  }

  const ritual = items[activeIndex];
  const description = ritual.short_description || ritual.description;

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-blush-500">Ритуал недели</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">{ritual.title}</h2>
        </div>
        <div className="flex gap-2">
          {items.map((item, index) => (
            <button
              key={item.id}
              type="button"
              onClick={() => setActiveIndex(index)}
              className={`h-2 w-2 rounded-full transition ${
                index === activeIndex ? "bg-blush-500" : "bg-blush-200"
              }`}
              aria-label={`Показать ритуал ${index + 1}`}
            />
          ))}
        </div>
      </div>
      <p className="text-sm text-ink-700">{description}</p>
      {ritual.cta_url ? (
        <Button href={ritual.cta_url} variant="ghost">
          {ritual.cta_text || "Записаться →"}
        </Button>
      ) : null}
    </div>
  );
}
