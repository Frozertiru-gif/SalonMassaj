"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { Service, ServiceCategory } from "@/lib/types";
import { deleteService, updateService } from "../../../actions";

type ServiceEditFormProps = {
  service: Service;
  categories: ServiceCategory[];
};

const initialState = { error: undefined, success: undefined };

export function ServiceEditForm({ service, categories }: ServiceEditFormProps) {
  const [updateState, updateAction] = useFormState(updateService, initialState);
  const [deleteState, deleteAction] = useFormState(deleteService, initialState);

  return (
    <div className="space-y-6">
      <Card>
        <h3 className="text-lg font-semibold text-ink-900">Редактировать услугу</h3>
        <form action={updateAction} className="mt-4 grid gap-4 md:grid-cols-2">
          <input type="hidden" name="id" value={service.id} />
          <div>
            <label className="text-xs font-medium text-ink-700">Категория</label>
            <select
              name="category_id"
              defaultValue={service.category_id}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm"
            >
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Название</label>
            <input
              name="title"
              required
              defaultValue={service.title}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Длительность (мин)</label>
            <input
              name="duration_min"
              type="number"
              required
              defaultValue={service.duration_min}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Цена от</label>
            <input
              name="price_from"
              type="number"
              required
              defaultValue={service.price_from}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Цена до</label>
            <input
              name="price_to"
              type="number"
              defaultValue={service.price_to ?? undefined}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Скидка (%)</label>
            <input
              name="discount_percent"
              type="number"
              min={0}
              max={100}
              defaultValue={service.discount_percent ?? undefined}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-xs font-medium text-ink-700">Короткое описание</label>
            <input
              name="short_description"
              required
              defaultValue={service.short_description}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div className="md:col-span-2">
            <label className="text-xs font-medium text-ink-700">Описание</label>
            <textarea
              name="description"
              required
              rows={4}
              defaultValue={service.description}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Изображение URL</label>
            <input
              name="image_url"
              defaultValue={service.image_url ?? undefined}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Теги (через запятую)</label>
            <input
              name="tags"
              defaultValue={service.tags.join(", ")}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">SEO Title</label>
            <input
              name="seo_title"
              defaultValue={service.seo_title ?? undefined}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">SEO Description</label>
            <input
              name="seo_description"
              defaultValue={service.seo_description ?? undefined}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-ink-700">Сортировка</label>
            <input
              name="sort_order"
              type="number"
              defaultValue={service.sort_order}
              className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
            />
          </div>
          <div className="flex items-center gap-2">
            <input name="is_active" type="checkbox" defaultChecked={service.is_active} />
            <label className="text-xs font-medium text-ink-700">Активна</label>
          </div>
          {updateState.error ? <p className="text-sm text-red-600 md:col-span-2">{updateState.error}</p> : null}
          {updateState.success ? <p className="text-sm text-green-600 md:col-span-2">{updateState.success}</p> : null}
          <div className="md:col-span-2">
            <Button type="submit">Сохранить</Button>
          </div>
        </form>
      </Card>
      <Card className="space-y-3">
        <h3 className="text-lg font-semibold text-ink-900">Удалить услугу</h3>
        <form action={deleteAction}>
          <input type="hidden" name="id" value={service.id} />
          <Button type="submit" variant="secondary">
            Удалить
          </Button>
        </form>
        {deleteState.error ? <p className="text-sm text-red-600">{deleteState.error}</p> : null}
        {deleteState.success ? <p className="text-sm text-green-600">{deleteState.success}</p> : null}
      </Card>
    </div>
  );
}
