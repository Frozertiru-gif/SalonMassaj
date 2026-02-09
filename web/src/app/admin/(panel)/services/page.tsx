import { adminFetch } from "@/lib/api";
import type { Service, ServiceCategory } from "@/lib/types";
import { Container } from "@/components/Container";
import { ServicesClient } from "./ServicesClient";

export default async function AdminServicesPage() {
  const services = await adminFetch<Service[]>("/admin/services");
  const categories = await adminFetch<ServiceCategory[]>("/admin/categories");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Услуги</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Каталог услуг</h2>
      </div>
      <ServicesClient services={services} categories={categories} />
    </Container>
  );
}
