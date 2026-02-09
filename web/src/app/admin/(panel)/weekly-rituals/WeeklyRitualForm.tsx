"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { WeeklyRitual } from "@/lib/types";
import type { AdminFormState } from "../../actions";

type WeeklyRitualFormProps = {
  action: (prevState: AdminFormState, formData: FormData) => Promise<AdminFormState>;
  initialData?: WeeklyRitual;
  submitLabel: string;
};

const initialState = { error: undefined, success: undefined };

export function WeeklyRitualForm({ action, initialData, submitLabel }: WeeklyRitualFormProps) {
  const [state, formAction] = useFormState(action, initialState);

  return (
    <Card>
      <form action={formAction} className="grid gap-4 md:grid-cols-2">
        {initialData ? <input type="hidden" name="id" value={initialData.id} /> : null}
        <div>
          <label className="text-xs font-medium text-ink-700">Название</label>
          <input
            name="title"
            required
            defaultValue={initialData?.title}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Slug</label>
          <input
            name="slug"
            defaultValue={initialData?.slug ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div className="md:col-span-2">
          <label className="text-xs font-medium text-ink-700">Короткое описание</label>
          <input
            name="short_description"
            defaultValue={initialData?.short_description ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div className="md:col-span-2">
          <label className="text-xs font-medium text-ink-700">Описание</label>
          <textarea
            name="description"
            required
            rows={4}
            defaultValue={initialData?.description}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Изображение URL</label>
          <input
            name="image_url"
            defaultValue={initialData?.image_url ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">CTA текст</label>
          <input
            name="cta_text"
            defaultValue={initialData?.cta_text ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">CTA ссылка</label>
          <input
            name="cta_url"
            defaultValue={initialData?.cta_url ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Дата начала</label>
          <input
            name="start_date"
            type="date"
            defaultValue={initialData?.start_date ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Дата окончания</label>
          <input
            name="end_date"
            type="date"
            defaultValue={initialData?.end_date ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Сортировка</label>
          <input
            name="sort_order"
            type="number"
            defaultValue={initialData?.sort_order ?? 0}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div className="flex items-center gap-2">
          <input name="is_active" type="checkbox" defaultChecked={initialData?.is_active ?? true} />
          <label className="text-xs font-medium text-ink-700">Активен</label>
        </div>
        {state.error ? <p className="text-sm text-red-600 md:col-span-2">{state.error}</p> : null}
        {state.success ? <p className="text-sm text-green-600 md:col-span-2">{state.success}</p> : null}
        <div className="md:col-span-2">
          <Button type="submit">{submitLabel}</Button>
        </div>
      </form>
    </Card>
  );
}
