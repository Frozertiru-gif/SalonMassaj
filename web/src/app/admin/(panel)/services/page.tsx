import { adminFetch } from "@/lib/api";
import { Container } from "@/components/Container";
import type { Service, ServiceCategory } from "@/lib/types";
import { ServicesClient } from "./ServicesClient";

export default async function AdminServicesPage() {
  const [services, categories] = await Promise.all([
    adminFetch<Service[]>("/admin/services"),
    adminFetch<ServiceCategory[]>("/admin/categories")
  ]);

  return (
    <Container className="space-y-6">
      <ServicesClient services={services} categories={categories} />
    </Container>
  );
}
