import { ReactNode } from "react";
import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { adminFetchResponse, ServiceUnavailableError } from "@/lib/api";
import { logoutAdmin } from "../actions";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  let authWarning: string | null = null;
  try {
    const response = await adminFetchResponse("/admin/auth/me", { currentPath: "/admin" });
    if (!response.ok) {
      authWarning = "Не удалось проверить сессию. Данные могут быть устаревшими.";
    }
  } catch (error) {
    if (error instanceof ServiceUnavailableError) {
      authWarning = "Не удалось проверить сессию. Данные могут быть устаревшими.";
    } else {
      throw error;
    }
  }

  return (
    <div className="min-h-screen bg-blush-50/40">
      <header className="border-b border-blush-100 bg-white">
        <Container className="flex flex-wrap items-center justify-between gap-4 py-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Админка</p>
            <h1 className="text-xl font-semibold text-ink-900">Salon Massaj</h1>
            {authWarning ? <p className="text-xs text-amber-600">{authWarning}</p> : null}
          </div>
          <nav className="flex flex-wrap gap-3 text-sm">
            <Button href="/admin" variant="ghost">
              Дашборд
            </Button>
            <Button href="/admin/services" variant="ghost">
              Услуги
            </Button>
            <Button href="/admin/categories" variant="ghost">
              Категории
            </Button>
            <Button href="/admin/weekly-rituals" variant="ghost">
              Ритуал недели
            </Button>
            <Button href="/admin/reviews" variant="ghost">
              Отзывы
            </Button>
            <Button href="/admin/bookings" variant="ghost">
              Записи
            </Button>
            <Button href="/admin/masters" variant="ghost">
              Мастера
            </Button>
            <Button href="/admin/settings" variant="ghost">
              Настройки
            </Button>
          </nav>
          <form action={logoutAdmin}>
            <Button type="submit" variant="secondary">
              Выйти
            </Button>
          </form>
        </Container>
      </header>
      <main className="py-8">{children}</main>
    </div>
  );
}
