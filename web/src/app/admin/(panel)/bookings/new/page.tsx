import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { adminFetch } from "@/lib/api";
import type { Service } from "@/lib/types";
import { AdminBookingCreateForm } from "../AdminBookingCreateForm";

export default async function AdminBookingsNewPage() {
  const services = await adminFetch<Service[]>("/admin/services");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Записи</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Записи / Новая запись</h2>
      </div>
      <Card className="space-y-3">
        <h3 className="text-lg font-semibold text-ink-900">Создать запись</h3>
        <AdminBookingCreateForm services={services} />
      </Card>
    </Container>
  );
}
