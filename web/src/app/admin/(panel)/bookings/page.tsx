import { adminFetch } from "@/lib/api";
import type { Booking } from "@/lib/types";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { updateBookingStatus } from "../../actions";

async function updateAction(formData: FormData) {
  "use server";
  const id = Number(formData.get("id"));
  const status = String(formData.get("status"));
  const is_read = formData.get("is_read") === "on";
  await updateBookingStatus(id, status, is_read);
}

export default async function AdminBookingsPage() {
  const bookings = await adminFetch<Booking[]>("/admin/bookings");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Записи</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Все записи</h2>
      </div>
      <div className="space-y-3">
        {bookings.map((booking) => (
          <Card key={booking.id} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-ink-900">{booking.client_name}</p>
                <p className="text-xs text-ink-500">{booking.client_phone}</p>
              </div>
              <div className="text-sm text-ink-600">{new Date(booking.starts_at).toLocaleString("ru-RU")}</div>
              <div className="text-xs uppercase tracking-[0.2em] text-blush-600">{booking.status}</div>
            </div>
            <form action={updateAction} className="flex flex-wrap gap-3 text-sm">
              <input type="hidden" name="id" value={booking.id} />
              <select name="status" defaultValue={booking.status} className="rounded-full border border-blush-100 px-3 py-2">
                <option value="NEW">NEW</option>
                <option value="CONFIRMED">CONFIRMED</option>
                <option value="CANCELLED">CANCELLED</option>
                <option value="DONE">DONE</option>
              </select>
              <label className="flex items-center gap-2">
                <input type="checkbox" name="is_read" defaultChecked={booking.is_read} />
                Прочитано
              </label>
              <Button type="submit" variant="secondary">
                Обновить
              </Button>
            </form>
          </Card>
        ))}
      </div>
    </Container>
  );
}
