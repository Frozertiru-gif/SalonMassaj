import { adminFetch } from "@/lib/api";
import type { Booking } from "@/lib/types";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";

export default async function AdminDashboardPage() {
  const bookings = await adminFetch<Booking[]>("/admin/bookings?unread=true");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Дашборд</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Новые записи</h2>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <p className="text-sm text-ink-600">Непрочитанные</p>
          <p className="mt-2 text-3xl font-semibold text-ink-900">{bookings.length}</p>
        </Card>
      </div>
      <div className="space-y-3">
        {bookings.length === 0 ? (
          <Card>Новых записей нет.</Card>
        ) : (
          bookings.map((booking) => (
            <Card key={booking.id} className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm text-ink-600">{booking.client_name}</p>
                <p className="text-sm text-ink-500">{booking.client_phone}</p>
              </div>
              <div className="text-sm text-ink-600">{new Date(booking.starts_at).toLocaleString("ru-RU")}</div>
              <div className="text-xs uppercase tracking-[0.2em] text-blush-600">{booking.status}</div>
            </Card>
          ))
        )}
      </div>
    </Container>
  );
}
