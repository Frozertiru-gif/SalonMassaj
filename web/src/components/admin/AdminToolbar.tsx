import { ReactNode } from "react";

type AdminToolbarProps = {
  children: ReactNode;
  stickyMobile?: boolean;
  className?: string;
};

export function AdminToolbar({ children, stickyMobile = false, className }: AdminToolbarProps) {
  return (
    <div
      className={`rounded-2xl border border-blush-100 bg-white/95 p-3 shadow-sm ${
        stickyMobile ? "sticky top-14 z-20 md:top-auto md:static" : ""
      } ${className ?? ""}`.trim()}
    >
      <div className="flex flex-col gap-3 md:flex-row md:flex-wrap md:items-end">{children}</div>
    </div>
  );
}
