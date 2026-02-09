"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { Review } from "@/lib/types";
import type { AdminFormState } from "../../actions";

type ReviewFormProps = {
  action: (prevState: AdminFormState, formData: FormData) => Promise<AdminFormState>;
  initialData?: Review;
  submitLabel: string;
};

const initialState = { error: undefined, success: undefined };

export function ReviewForm({ action, initialData, submitLabel }: ReviewFormProps) {
  const [state, formAction] = useFormState(action, initialState);

  return (
    <Card>
      <form action={formAction} className="grid gap-4 md:grid-cols-2">
        {initialData ? <input type="hidden" name="id" value={initialData.id} /> : null}
        <div>
          <label className="text-xs font-medium text-ink-700">Автор</label>
          <input
            name="author_name"
            required
            defaultValue={initialData?.author_name}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Оценка (1-5)</label>
          <input
            name="rating"
            type="number"
            min={1}
            max={5}
            defaultValue={initialData?.rating ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div className="md:col-span-2">
          <label className="text-xs font-medium text-ink-700">Текст</label>
          <textarea
            name="text"
            required
            rows={4}
            defaultValue={initialData?.text}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Источник</label>
          <input
            name="source"
            defaultValue={initialData?.source ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Ссылка на источник</label>
          <input
            name="source_url"
            defaultValue={initialData?.source_url ?? undefined}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Дата отзыва</label>
          <input
            name="review_date"
            type="date"
            defaultValue={initialData?.review_date ?? undefined}
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
          <input name="is_published" type="checkbox" defaultChecked={initialData?.is_published ?? true} />
          <label className="text-xs font-medium text-ink-700">Опубликован</label>
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
