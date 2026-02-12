import { adminFetch } from "@/lib/api";
import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import type { Service } from "@/lib/types";
import { ServicesClient } from "./ServicesClient";

export default async function AdminServicesPage() {
  const services = await adminFetch<Service[]>("/admin/services");

  return (
    <Container className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Услуги</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">Каталог услуг</h2>
        </div>
        <Button href="/admin/services/new" variant="secondary">
          Добавить
        </Button>
      </div>
      <ServicesClient services={services} />
    </Container>
  );
}
