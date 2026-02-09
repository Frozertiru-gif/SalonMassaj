import type { ReactNode } from "react";

interface BadgeProps {
  children: ReactNode;
}

export function Badge({ children }: BadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full bg-blush-100 px-3 py-1 text-xs font-medium text-blush-700">
      {children}
    </span>
  );
}
