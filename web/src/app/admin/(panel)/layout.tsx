import { ReactNode } from "react";
import { Button } from "@/components/Button";
import { adminFetchResponse, ServiceUnavailableError } from "@/lib/api";
import type { AdminProfile } from "@/lib/types";
import { AdminShell } from "@/components/admin/AdminShell";
import { logoutAdmin } from "../actions";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  let authWarning: string | null = null;
  let adminProfile: AdminProfile | null = null;
  try {
    const response = await adminFetchResponse("/admin/auth/me", { currentPath: "/admin" });
    if (!response.ok) {
      authWarning = "Не удалось проверить сессию. Данные могут быть устаревшими.";
    } else {
      adminProfile = (await response.json()) as AdminProfile;
    }
  } catch (error) {
    if (error instanceof ServiceUnavailableError) {
      authWarning = "Не удалось проверить сессию. Данные могут быть устаревшими.";
    } else {
      throw error;
    }
  }

  return (
    <AdminShell
      authWarning={authWarning}
      role={adminProfile?.role}
      logoutNode={
        <form action={logoutAdmin}>
          <Button type="submit" variant="secondary" className="w-full md:w-auto">
            Выйти
          </Button>
        </form>
      }
    >
      {children}
    </AdminShell>
  );
}
