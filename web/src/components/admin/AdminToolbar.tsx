import type { ReactNode } from "react";

export function AdminToolbar({ children, stickyMobile = false }: { children: ReactNode; stickyMobile?: boolean }) {
  return (
    <div
      className={`z-10 rounded-2xl border border-blush-100 bg-white p-3 shadow-sm md:p-4 ${stickyMobile ? "sticky top-16" : ""}`}
    >
      <div className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-end md:gap-4">{children}</div>
    </div>
  );
}
