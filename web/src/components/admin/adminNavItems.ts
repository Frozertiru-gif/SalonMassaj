export type AdminNavItem = {
  href: string;
  label: string;
  shortLabel: string;
  icon: string;
};

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  { href: "/admin", label: "Дашборд", shortLabel: "Дашборд", icon: "📊" },
  { href: "/admin/services", label: "Услуги", shortLabel: "Услуги", icon: "💆" },
  { href: "/admin/categories", label: "Категории", shortLabel: "Категории", icon: "🗂️" },
  { href: "/admin/weekly-rituals", label: "Ритуал недели", shortLabel: "Ритуал", icon: "✨" },
  { href: "/admin/reviews", label: "Отзывы", shortLabel: "Отзывы", icon: "💬" },
  { href: "/admin/bookings", label: "Записи", shortLabel: "Записи", icon: "🗓️" },
  { href: "/admin/schedule", label: "Расписание", shortLabel: "График", icon: "🕒" },
  { href: "/admin/masters", label: "Мастера", shortLabel: "Мастера", icon: "🧑‍🔧" },
  { href: "/admin/settings", label: "Настройки", shortLabel: "Настройки", icon: "⚙️" },
  { href: "/admin/logs", label: "Логи", shortLabel: "Логи", icon: "📜" }
];
