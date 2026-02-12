"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { WeeklyRitual } from "@/lib/types";
import { deleteWeeklyRitual } from "../../actions";

type WeeklyRitualListProps = {
  rituals: WeeklyRitual[];
};

const initialState = { error: undefined, success: undefined };

export function WeeklyRitualList({ rituals }: WeeklyRitualListProps) {
  if (rituals.length === 0) {
    return <Card>Пока нет ритуалов недели.</Card>;
  }

  return (
    <div className="space-y-3">
      {rituals.map((ritual) => (
        <WeeklyRitualRow key={ritual.id} ritual={ritual} />
      ))}
    </div>
  );
}

function WeeklyRitualRow({ ritual }: { ritual: WeeklyRitual }) {
  const [deleteState, deleteAction] = useFormState(deleteWeeklyRitual, initialState);

  return (
    <Card className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-ink-900">{ritual.title}</p>
      </div>
      <div className="text-xs uppercase tracking-[0.2em] text-blush-600">
        {ritual.is_active ? "Активен" : "Выключен"}
      </div>
      <div className="flex items-center gap-3">
        <Button href={`/admin/weekly-rituals/${ritual.id}`} variant="ghost">
          Редактировать
        </Button>
        <form action={deleteAction}>
          <input type="hidden" name="id" value={ritual.id} />
          <Button type="submit" variant="secondary">
            Удалить
          </Button>
        </form>
      </div>
      {deleteState.error ? <p className="text-sm text-red-600 w-full">{deleteState.error}</p> : null}
      {deleteState.success ? <p className="text-sm text-green-600 w-full">{deleteState.success}</p> : null}
    </Card>
  );
}
