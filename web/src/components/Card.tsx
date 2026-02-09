import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

export function Card({ children, className }: CardProps) {
  return (
    <div
      className={`rounded-2xl bg-white/90 p-6 shadow-card backdrop-blur-sm ring-1 ring-blush-100 ${
        className ?? ""
      }`.trim()}
    >
      {children}
    </div>
  );
}
