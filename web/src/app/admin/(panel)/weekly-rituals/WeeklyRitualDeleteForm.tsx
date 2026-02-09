"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import type { AdminFormState } from "../../actions";
import { deleteWeeklyRitual } from "../../actions";

type WeeklyRitualDeleteFormProps = {
  ritualId: number;
};

const initialState: AdminFormState = { error: undefined, success: undefined };

export function WeeklyRitualDeleteForm({ ritualId }: WeeklyRitualDeleteFormProps) {
  const [state, action] = useFormState(deleteWeeklyRitual, initialState);

  return (
    <form action={action} className="space-y-2">
      <input type="hidden" name="id" value={ritualId} />
      <Button type="submit" variant="secondary">
        Удалить
      </Button>
      {state.error ? <p className="text-sm text-red-600">{state.error}</p> : null}
      {state.success ? <p className="text-sm text-green-600">{state.success}</p> : null}
    </form>
  );
}
