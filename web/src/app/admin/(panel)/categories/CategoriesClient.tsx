"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { ServiceCategory } from "@/lib/types";
import { createCategory, deleteCategory, updateCategory } from "../../actions";

type CategoriesClientProps = {
  categories: ServiceCategory[];
};

const initialState = { error: undefined, success: undefined };

export function CategoriesClient({ categories }: CategoriesClientProps) {
  const [createState, createAction] = useFormState(createCategory, initialState);

  return (
    <>
      <Card>
        <h3 className="text-lg font-semibold text-ink-900">Добавить категорию</h3>
        <form action={createAction} className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-xs font-medium text-ink-700">Название</label>
            <input name="title" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3" />
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
      <div className="space-y-3">
        {categories.map((category) => (
          <CategoryRow key={category.id} category={category} />
        ))}
      </div>
    </>
  );
}

function CategoryRow({ category }: { category: ServiceCategory }) {
  const [updateState, updateAction] = useFormState(updateCategory, initialState);
  const [deleteState, deleteAction] = useFormState(deleteCategory, initialState);

  return (
    <Card className="space-y-4">
      <form action={updateAction} className="grid gap-4 md:grid-cols-2">
        <input type="hidden" name="id" value={category.id} />
        <div>
          <label className="text-xs font-medium text-ink-700">Название</label>
          <input
            name="title"
            required
            defaultValue={category.title}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-ink-700">Сортировка</label>
          <input
            name="sort_order"
            type="number"
            defaultValue={category.sort_order}
            className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3"
          />
        </div>
        <div className="flex items-center gap-2">
          <input name="is_active" type="checkbox" defaultChecked={category.is_active} />
          <label className="text-xs font-medium text-ink-700">Активна</label>
        </div>
        {updateState.error ? <p className="text-sm text-red-600 md:col-span-2">{updateState.error}</p> : null}
        {updateState.success ? <p className="text-sm text-green-600 md:col-span-2">{updateState.success}</p> : null}
        <div className="md:col-span-2">
          <Button type="submit" variant="secondary">
            Сохранить
          </Button>
        </div>
      </form>
      <form action={deleteAction} className="flex items-center justify-between gap-3 border-t border-blush-100 pt-4">
        <input type="hidden" name="id" value={category.id} />
        <p className="text-xs text-ink-500">Удаление категории невозможно, если в ней есть услуги.</p>
        <Button type="submit" variant="ghost">
          Удалить
        </Button>
      </form>
      {deleteState.error ? <p className="text-sm text-red-600">{deleteState.error}</p> : null}
      {deleteState.success ? <p className="text-sm text-green-600">{deleteState.success}</p> : null}
    </Card>
  );
}
