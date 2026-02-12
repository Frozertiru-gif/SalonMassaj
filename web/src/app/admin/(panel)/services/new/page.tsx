import { Container } from "@/components/Container";
import { adminFetch } from "@/lib/api";
import type { ServiceCategory } from "@/lib/types";
import { ServiceCreateForm } from "./ServiceCreateForm";

export default async function ServiceNewPage() {
  const categories = await adminFetch<ServiceCategory[]>("/admin/categories");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Услуги</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Услуги / Новая услуга</h2>
      </div>
      <ServiceCreateForm categories={categories} />
    </Container>
  );
}
