import { adminFetch } from "@/lib/api";
import type { ServiceCategory } from "@/lib/types";
import { Container } from "@/components/Container";
import { CategoriesClient } from "./CategoriesClient";

export default async function AdminCategoriesPage() {
  const categories = await adminFetch<ServiceCategory[]>("/admin/categories");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Категории</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Категории услуг</h2>
      </div>
      <CategoriesClient categories={categories} />
    </Container>
  );
}
