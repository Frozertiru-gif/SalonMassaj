"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ADMIN_NAV_ITEMS } from "./adminNavItems";

function isActive(pathname: string, href: string) {
  if (href === "/admin") return pathname === "/admin";
  return pathname.startsWith(href);
}

export function AdminNav({
  mobile = false,
  showLogs,
  onNavigate
}: {
  mobile?: boolean;
  showLogs: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const items = ADMIN_NAV_ITEMS.filter((item) => (item.href === "/admin/logs" ? showLogs : true));

  if (mobile) {
    return (
      <nav className="grid grid-cols-1 gap-2 sm:grid-cols-2" aria-label="Навигация админки">
        {items.map((item) => {
          const active = isActive(pathname, item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm transition ${active
                ? "border-blush-300 bg-blush-100 text-ink-900"
                : "border-blush-100 bg-white text-ink-700 hover:border-blush-200 hover:bg-blush-50"
                }`}
            >
              <span aria-hidden>{item.icon}</span>
              <span>{item.shortLabel}</span>
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav className="flex flex-wrap items-center gap-2 text-sm" aria-label="Навигация админки">
      {items.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`inline-flex items-center rounded-full px-4 py-2 transition ${active
              ? "bg-blush-200 text-ink-900"
              : "text-ink-700 hover:bg-blush-100 hover:text-blush-700"
              }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
