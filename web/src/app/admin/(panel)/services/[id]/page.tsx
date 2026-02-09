import { notFound } from "next/navigation";
import { adminFetch } from "@/lib/api";
import type { Service, ServiceCategory } from "@/lib/types";
import { Container } from "@/components/Container";
import { ServiceEditForm } from "./ServiceEditForm";

type ServiceEditPageProps = {
  params: { id: string };
};

export default async function ServiceEditPage({ params }: ServiceEditPageProps) {
  const serviceId = Number(params.id);
  if (Number.isNaN(serviceId)) {
    notFound();
  }

  let service: Service | null = null;
  try {
    const services = await adminFetch<Service[]>("/admin/services");
    service = services.find((item) => item.id === serviceId) ?? null;
  } catch {
    service = null;
  }

  if (!service) {
    notFound();
  }

  const categories = await adminFetch<ServiceCategory[]>("/admin/categories");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Услуги</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Редактирование услуги</h2>
      </div>
      <ServiceEditForm service={service} categories={categories} />
    </Container>
  );
}
