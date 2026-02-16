"use client";

import { ReactNode, useMemo, useState } from "react";
import { usePathname } from "next/navigation";
import { Container } from "@/components/Container";
import { AdminNav, getAdminPageTitle } from "./AdminNav";
import { MobileAdminHeader } from "./MobileAdminHeader";

export function AdminShell({
  children,
  authWarning,
  role,
  logoutNode
}: {
  children: ReactNode;
  authWarning: string | null;
  role?: "ADMIN" | "SYS_ADMIN";
  logoutNode: ReactNode;
}) {
  const pathname = usePathname();
  const title = useMemo(() => getAdminPageTitle(pathname), [pathname]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-blush-50/40">
      <MobileAdminHeader title={title} onMenuOpen={() => setMobileMenuOpen(true)} />

      <header className="hidden border-b border-blush-100 bg-white md:block">
        <Container className="flex items-center justify-between gap-4 py-4">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-[0.3em] text-blush-600">Админка</p>
            <h1 className="text-xl font-semibold text-ink-900">Salon Massaj</h1>
            {authWarning ? <p className="text-xs text-amber-600">{authWarning}</p> : null}
          </div>
          <AdminNav role={role} />
          <div>{logoutNode}</div>
        </Container>
      </header>

      {mobileMenuOpen ? (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal>
          <button
            type="button"
            className="absolute inset-0 bg-black/40"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Закрыть меню"
          />
          <aside className="relative ml-auto flex h-full w-[85%] max-w-sm flex-col gap-4 bg-white p-4 shadow-2xl">
            <div className="flex items-start justify-between gap-3 border-b border-blush-100 pb-3">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-blush-600">Админка</p>
                <p className="text-lg font-semibold text-ink-900">Salon Massaj</p>
                {authWarning ? <p className="text-xs text-amber-600">{authWarning}</p> : null}
              </div>
              <button
                type="button"
                className="rounded-lg border border-blush-100 px-3 py-1 text-sm"
                onClick={() => setMobileMenuOpen(false)}
              >
                ✕
              </button>
            </div>
            <AdminNav role={role} mode="mobile" onNavigate={() => setMobileMenuOpen(false)} />
            <div className="mt-auto border-t border-blush-100 pt-4" onClick={() => setMobileMenuOpen(false)}>
              {logoutNode}
            </div>
          </aside>
        </div>
      ) : null}

      <main className="pb-8 pt-[72px] md:pt-8">{children}</main>
    </div>
  );
}
