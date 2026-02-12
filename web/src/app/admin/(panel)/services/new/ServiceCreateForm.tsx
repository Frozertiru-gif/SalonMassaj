"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { ServiceCategory } from "@/lib/types";
import { createService } from "../../../actions";

const initialState = { error: undefined, success: undefined };

export function ServiceCreateForm({ categories }: { categories: ServiceCategory[] }) {
  const [createState, createAction] = useFormState(createService, initialState);

  return (
    <Card>
      <form action={createAction} className="grid gap-4 md:grid-cols-2">
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
        <div>
          <label className="text-xs font-medium text-ink-700">Скидка (%)</label>
          <input name="discount_percent" type="number" min={0} max={100} className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
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
        {createState.error ? <p className="text-sm text-red-600 md:col-span-2">{createState.error}</p> : null}
        {createState.success ? <p className="text-sm text-green-600 md:col-span-2">{createState.success}</p> : null}
        <div className="md:col-span-2">
          <Button type="submit">Создать</Button>
        </div>
      </form>
    </Card>
  );
}
