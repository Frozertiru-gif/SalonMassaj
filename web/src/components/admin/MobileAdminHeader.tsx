"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/Button";
import { logoutAdmin } from "@/app/admin/actions";
import { AdminNav } from "./AdminNav";
import { ADMIN_NAV_ITEMS } from "./adminNavItems";

function getTitle(pathname: string): string {
  const matched = [...ADMIN_NAV_ITEMS]
    .sort((a, b) => b.href.length - a.href.length)
    .find((item) => (item.href === "/admin" ? pathname === "/admin" : pathname.startsWith(item.href)));
  return matched?.label ?? "Админка";
}

export function MobileAdminHeader({ showLogs }: { showLogs: boolean }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const body = document.body;
    body.style.overflow = "hidden";
    return () => {
      body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-40 h-14 border-b border-blush-100 bg-white/95 backdrop-blur md:hidden">
        <div className="flex h-full items-center justify-between px-4">
          <button
            type="button"
            aria-label="Открыть меню"
            className="rounded-lg border border-blush-100 px-3 py-2 text-sm"
            onClick={() => setOpen(true)}
          >
            ☰
          </button>
          <p className="max-w-[60%] truncate text-sm font-semibold text-ink-900">{getTitle(pathname)}</p>
          <span className="w-10" aria-hidden />
        </div>
      </header>

      {open ? (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-black/35"
            aria-label="Закрыть меню"
            onClick={() => setOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-[86%] max-w-sm overflow-y-auto bg-white p-4 shadow-xl">
            <div className="mb-4 border-b border-blush-100 pb-4">
              <p className="text-xs uppercase tracking-[0.2em] text-blush-600">Админка</p>
              <p className="text-lg font-semibold text-ink-900">Salon Massaj</p>
            </div>
            <AdminNav mobile showLogs={showLogs} onNavigate={() => setOpen(false)} />
            <form action={logoutAdmin} className="mt-4 border-t border-blush-100 pt-4">
              <Button type="submit" variant="secondary" className="w-full">
                Выйти
              </Button>
            </form>
          </div>
        </div>
      ) : null}
    </>
  );
}
