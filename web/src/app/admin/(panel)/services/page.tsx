import { adminFetch } from "@/lib/api";
import type { Service, ServiceCategory } from "@/lib/types";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { createService } from "../../actions";

export default async function AdminServicesPage() {
  const services = await adminFetch<Service[]>("/admin/services");
  const categories = await adminFetch<ServiceCategory[]>("/admin/categories");

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Услуги</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Каталог услуг</h2>
      </div>
      <Card>
        <h3 className="text-lg font-semibold text-ink-900">Добавить услугу</h3>
        <form action={createService} className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs font-medium text-ink-700">Категория</label>
            <select name="category_id" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm">
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Название</label>
            <input name="title" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Slug</label>
            <input name="slug" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Длительность (мин)</label>
            <input name="duration_min" type="number" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Цена от</label>
            <input name="price_from" type="number" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Цена до</label>
            <input name="price_to" type="number" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div className="md:col-span-2">
            <label className="text-xs font-medium text-ink-700">Короткое описание</label>
            <input name="short_description" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div className="md:col-span-2">
            <label className="text-xs font-medium text-ink-700">Описание</label>
            <textarea name="description" required rows={4} className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Изображение URL</label>
            <input name="image_url" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Теги (через запятую)</label>
            <input name="tags" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">SEO Title</label>
            <input name="seo_title" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">SEO Description</label>
            <input name="seo_description" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
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
        {services.map((service) => (
          <Card key={service.id} className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-ink-900">{service.title}</p>
              <p className="text-xs text-ink-500">{service.slug}</p>
            </div>
            <div className="text-sm text-ink-600">{service.duration_min} мин</div>
            <div className="text-sm text-ink-600">от {service.price_from} ₽</div>
          </Card>
        ))}
      </div>
    </Container>
  );
}
