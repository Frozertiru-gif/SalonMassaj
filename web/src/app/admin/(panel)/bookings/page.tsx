import { adminFetch } from "@/lib/api";
import type { Booking, Master, Service } from "@/lib/types";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { BookingsCreateSection } from "./BookingsCreateSection";
import { BookingUpdateForm } from "./BookingUpdateForm";


function formatPrice(cents?: number | null) {
  if (cents == null) return "—";
  return `${(cents / 100).toLocaleString("ru-RU")} ₽`;
}

const STATUS_LABELS: Record<string, string> = {
  NEW: "Новая",
  CONFIRMED: "Подтверждено",
  CANCELLED: "Отменено",
  DONE: "Завершено"
};

const TABS = [
  { key: "new", label: "Новые" },
  { key: "active", label: "Активные" },
  { key: "completed", label: "Завершенные" },
  { key: "all", label: "Все" }
] as const;

function buildBookingsPath(searchParams: Record<string, string | undefined>) {
  const params = new URLSearchParams();
  if (searchParams.status) params.set("status", searchParams.status);
  if (searchParams.unread) params.set("unread", searchParams.unread);
  if (searchParams.date_from) params.set("date_from", searchParams.date_from);
  if (searchParams.date_to) params.set("date_to", searchParams.date_to);
  if (searchParams.service_id) params.set("service_id", searchParams.service_id);
  if (searchParams.master_id) params.set("master_id", searchParams.master_id);
  if (searchParams.q) params.set("q", searchParams.q);
  const q = params.toString();
  return q ? `/admin/bookings?${q}` : "/admin/bookings";
}

export default async function AdminBookingsPage({ searchParams }: { searchParams: Record<string, string | undefined> }) {
  const tab = searchParams.tab ?? "new";
  const tabQuery: Record<string, string | undefined> = { ...searchParams };
  if (tab === "new") {
    tabQuery.status = "NEW";
    tabQuery.unread = "true";
  } else if (tab === "active") {
    tabQuery.status = "CONFIRMED";
  } else if (tab === "completed") {
    tabQuery.status = "DONE";
  } else {
    delete tabQuery.status;
    delete tabQuery.unread;
  }

  const [bookings, services, masters] = await Promise.all([
    adminFetch<Booking[]>(buildBookingsPath(tabQuery)),
    adminFetch<Service[]>("/admin/services"),
    adminFetch<Master[]>("/admin/masters")
  ]);

  return (
    <Container className="space-y-6">
      <BookingsCreateSection services={services} />

      <Card className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {TABS.map((item) => (
            <a key={item.key} href={`/admin/bookings?tab=${item.key}`} className={`rounded-full px-4 py-2 text-sm ${tab === item.key ? "bg-blush-200" : "bg-white border border-blush-100"}`}>
              {item.label}
            </a>
          ))}
        </div>
        <form className="grid gap-3 md:grid-cols-3" method="GET">
          <input type="hidden" name="tab" value={tab} />
          <input name="q" defaultValue={searchParams.q} placeholder="Поиск: имя или телефон" className="rounded-2xl border border-blush-100 px-4 py-2 text-sm" />
          <input name="date_from" type="date" defaultValue={searchParams.date_from} className="rounded-2xl border border-blush-100 px-4 py-2 text-sm" />
          <input name="date_to" type="date" defaultValue={searchParams.date_to} className="rounded-2xl border border-blush-100 px-4 py-2 text-sm" />
          <select name="service_id" defaultValue={searchParams.service_id} className="rounded-2xl border border-blush-100 px-4 py-2 text-sm">
            <option value="">Все услуги</option>
            {services.map((service) => <option key={service.id} value={service.id}>{service.title}</option>)}
          </select>
          <select name="master_id" defaultValue={searchParams.master_id} className="rounded-2xl border border-blush-100 px-4 py-2 text-sm">
            <option value="">Все мастера</option>
            {masters.map((master) => <option key={master.id} value={master.id}>{master.name}</option>)}
          </select>
          <button className="rounded-full bg-blush-200 px-4 py-2 text-sm font-medium" type="submit">Применить</button>
        </form>
      </Card>


      <div className="space-y-3">
        <div className="mb-2 hidden grid-cols-[minmax(120px,1.2fr)_minmax(140px,1.2fr)_minmax(130px,1fr)_minmax(120px,0.8fr)] gap-3 px-2 text-xs font-semibold uppercase tracking-[0.15em] text-ink-500 md:grid">
          <span>Клиент</span>
          <span>Дата и услуга</span>
          <span>Статус/мастер</span>
          <span>Итоговая цена</span>
        </div>
        {bookings.map((booking) => (
          <Card key={booking.id} className="space-y-3">
            <div className="grid gap-2 text-sm md:grid-cols-[minmax(120px,1.2fr)_minmax(140px,1.2fr)_minmax(130px,1fr)_minmax(120px,0.8fr)]">
              <div>
                <p className="font-medium text-ink-900">{booking.client_name}</p>
                <p className="text-ink-500">{booking.client_phone}</p>
              </div>
              <div>
                <p>{new Date(booking.starts_at).toLocaleString("ru-RU")}</p>
                <p className="text-ink-500">{booking.service?.title ?? `Услуга #${booking.service_id}`}</p>
              </div>
              <div>
                <p>Мастер: {booking.master?.name ?? "Не назначен"}</p>
                <p className="text-xs uppercase tracking-[0.2em] text-blush-600">{STATUS_LABELS[booking.status] ?? booking.status}</p>
              </div>
              <div>
                <p className="font-medium text-ink-900">{formatPrice(booking.final_price_cents)}</p>
                <p className="text-xs text-ink-500">Фактическая стоимость</p>
              </div>
            </div>
            <div className="rounded-2xl border border-blush-100 bg-blush-50/40 px-3 py-2">
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-ink-500">Комментарий клиента</p>
              <p className="mt-1 text-sm text-ink-900">{booking.comment?.trim() ? booking.comment : "—"}</p>
            </div>
            <BookingUpdateForm booking={booking} masters={masters} />
          </Card>
        ))}
      </div>
    </Container>
  );
}
