import { ReactNode } from "react";
import { Container } from "@/components/Container";
import type { AdminProfile } from "@/lib/types";
import { logoutAdmin } from "@/app/admin/actions";
import { AdminNav } from "./AdminNav";
import { MobileAdminHeader } from "./MobileAdminHeader";

export function AdminShell({
  children,
  authWarning,
  adminProfile
}: {
  children: ReactNode;
  authWarning: string | null;
  adminProfile: AdminProfile | null;
}) {
  const showLogs = adminProfile?.role === "SYS_ADMIN";

  return (
    <div className="min-h-screen bg-blush-50/40">
      <MobileAdminHeader showLogs={showLogs} />

      <header className="hidden border-b border-blush-100 bg-white md:block">
        <Container className="space-y-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Админка</p>
              <h1 className="text-xl font-semibold text-ink-900">Salon Massaj</h1>
              {authWarning ? <p className="text-xs text-amber-600">{authWarning}</p> : null}
            </div>
            <form action={logoutAdmin}>
              <button
                type="submit"
                className="rounded-full border border-blush-200 bg-white px-6 py-3 text-sm font-medium text-blush-700 transition hover:border-blush-300"
              >
                Выйти
              </button>
            </form>
          </div>
          <AdminNav showLogs={showLogs} />
        </Container>
      </header>

      <main className="py-4 pt-[calc(56px+1rem)] md:py-8 md:pt-8">
        {authWarning ? (
          <Container className="mb-3 md:hidden">
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">{authWarning}</p>
          </Container>
        ) : null}
        {children}
      </main>
    </div>
  );
}
