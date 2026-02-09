import { adminFetch } from "@/lib/api";
import type { ServiceCategory } from "@/lib/types";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { createCategory } from "../../actions";

export default async function AdminCategoriesPage() {
  const categories = await adminFetch<ServiceCategory[]>("/admin/categories");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Категории</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Категории услуг</h2>
      </div>
      <Card>
        <h3 className="text-lg font-semibold text-ink-900">Добавить категорию</h3>
        <form action={createCategory} className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs font-medium text-ink-700">Название</label>
            <input name="title" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Slug</label>
            <input name="slug" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Сортировка</label>
            <input name="sort_order" type="number" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div className="flex items-center gap-2">
            <input name="is_active" type="checkbox" defaultChecked />
            <label className="text-xs font-medium text-ink-700">Активна</label>
          </div>
          <div className="md:col-span-2">
            <Button type="submit">Создать</Button>
          </div>
        </form>
      </Card>
      <div className="space-y-3">
        {categories.map((category) => (
          <Card key={category.id} className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-ink-900">{category.title}</p>
              <p className="text-xs text-ink-500">{category.slug}</p>
            </div>
            <div className="text-sm text-ink-600">#{category.sort_order}</div>
          </Card>
        ))}
      </div>
    </Container>
  );
}
