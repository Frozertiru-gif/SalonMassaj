import { ReactNode } from "react";
import { adminFetchResponse, ServiceUnavailableError } from "@/lib/api";
import type { AdminProfile } from "@/lib/types";
import { AdminShell } from "@/components/admin/AdminShell";

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
    <AdminShell authWarning={authWarning} adminProfile={adminProfile}>
      {children}
    </AdminShell>
  );
}
