"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type AdminNavItem = {
  href: string;
  label: string;
  shortLabel: string;
  icon: string;
  roles?: Array<"ADMIN" | "SYS_ADMIN">;
};

const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  { href: "/admin", label: "Дашборд", shortLabel: "Дашборд", icon: "🏠" },
  { href: "/admin/services", label: "Услуги", shortLabel: "Услуги", icon: "💆" },
  { href: "/admin/categories", label: "Категории", shortLabel: "Категории", icon: "🗂" },
  { href: "/admin/weekly-rituals", label: "Ритуал недели", shortLabel: "Ритуал", icon: "✨" },
  { href: "/admin/reviews", label: "Отзывы", shortLabel: "Отзывы", icon: "💬" },
  { href: "/admin/bookings", label: "Записи", shortLabel: "Записи", icon: "📋" },
  { href: "/admin/schedule", label: "Расписание", shortLabel: "График", icon: "🗓" },
  { href: "/admin/masters", label: "Мастера", shortLabel: "Мастера", icon: "🧑‍🔧" },
  { href: "/admin/settings", label: "Настройки", shortLabel: "Настройки", icon: "⚙️" },
  { href: "/admin/logs", label: "Логи", shortLabel: "Логи", icon: "🧾", roles: ["SYS_ADMIN"] }
];

export function getAdminPageTitle(pathname: string): string {
  const sorted = [...ADMIN_NAV_ITEMS].sort((a, b) => b.href.length - a.href.length);
  const active = sorted.find((item) => pathname === item.href || pathname.startsWith(`${item.href}/`));
  return active?.label ?? "Админка";
}

export function AdminNav({
  role,
  mode = "desktop",
  onNavigate
}: {
  role?: "ADMIN" | "SYS_ADMIN";
  mode?: "desktop" | "mobile";
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const visibleItems = ADMIN_NAV_ITEMS.filter((item) => !item.roles || (role && item.roles.includes(role)));

  if (mode === "mobile") {
    return (
      <nav className="grid grid-cols-1 gap-2 sm:grid-cols-2" aria-label="Навигация админки">
        {visibleItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={`flex items-center gap-2 rounded-2xl border px-3 py-3 text-sm transition ${
                isActive
                  ? "border-blush-300 bg-blush-100 text-blush-800"
                  : "border-blush-100 bg-white text-ink-700 hover:border-blush-200 hover:text-blush-700"
              }`}
            >
              <span aria-hidden>{item.icon}</span>
              <span className="font-medium">{item.shortLabel}</span>
            </Link>
          );
        })}
      </nav>
    );
  }

  return (
    <nav className="flex flex-wrap items-center gap-2 text-sm" aria-label="Навигация админки">
      {visibleItems.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`rounded-full px-4 py-2 transition ${
              isActive ? "bg-blush-200 text-blush-800" : "text-ink-700 hover:bg-blush-50 hover:text-blush-700"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
