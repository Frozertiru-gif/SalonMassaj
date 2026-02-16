import { ReactNode } from "react";
import { Button } from "@/components/Button";
import { ServiceUnavailableError } from "@/lib/api";
import { AdminShell } from "@/components/admin/AdminShell";
import { logoutAdmin } from "../actions";
import { getCurrentAdmin } from "../adminApi";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  let authWarning: string | null = null;
  let adminProfile: Awaited<ReturnType<typeof getCurrentAdmin>> | null = null;
  try {
    adminProfile = await getCurrentAdmin();
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
