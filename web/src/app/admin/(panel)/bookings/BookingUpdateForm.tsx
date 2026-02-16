"use client";

import { useFormState, useFormStatus } from "react-dom";
import type { Booking, Master } from "@/lib/types";
import { updateBookingAdminFormAction, type UpdateBookingActionState } from "../../actions";

type BookingUpdateFormProps = {
  booking: Booking;
  masters: Master[];
};

function formatDateTimeLocal(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (num: number) => String(num).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <button type="submit" className="rounded-full bg-blush-100 px-4 py-2 text-sm disabled:opacity-60" disabled={pending}>
      {pending ? "Сохранение..." : "Сохранить / перенести запись"}
    </button>
  );
}

const INITIAL_STATE: UpdateBookingActionState = { ok: true };

export function BookingUpdateForm({ booking, masters }: BookingUpdateFormProps) {
  const [state, action] = useFormState(updateBookingAdminFormAction, INITIAL_STATE);

  return (
    <form action={action} className="grid gap-2 md:grid-cols-4">
      <input type="hidden" name="id" value={booking.id} />
      <select name="status" defaultValue={booking.status} className="rounded-full border border-blush-100 px-3 py-2 text-sm">
        <option value="NEW">Новая</option>
        <option value="CONFIRMED">Подтверждено</option>
        <option value="CANCELLED">Отменено</option>
        <option value="DONE">Завершено</option>
      </select>
      <select name="master_id" defaultValue={booking.master?.id ?? ""} className="rounded-full border border-blush-100 px-3 py-2 text-sm">
        <option value="">Не назначен</option>
        {masters.map((master) => <option key={master.id} value={master.id}>{master.name}</option>)}
      </select>
      <input
        name="starts_at"
        type="datetime-local"
        defaultValue={formatDateTimeLocal(booking.starts_at)}
        className="rounded-full border border-blush-100 px-3 py-2 text-sm"
      />
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="is_read" defaultChecked={booking.is_read} />Прочитано</label>
      <div className="space-y-1">
        <input
          name="final_price_rub"
          type="number"
          min="0"
          step="1"
          defaultValue={booking.final_price_cents != null ? String(booking.final_price_cents / 100) : ""}
          placeholder="Фактическая стоимость, ₽"
          required={booking.status === "DONE"}
          className="w-full rounded-full border border-blush-100 px-3 py-2 text-sm"
        />
        {booking.status === "DONE" && <p className="text-xs text-ink-500">Для статуса «Завершено» укажите цену больше 0.</p>}
      </div>
      <SubmitButton />
      {state.error && <p className="md:col-span-4 text-sm text-red-600">{state.error}</p>}
      <textarea name="admin_comment" defaultValue={booking.admin_comment ?? ""} placeholder="Комментарий админа" className="md:col-span-4 rounded-2xl border border-blush-100 px-3 py-2 text-sm" />
    </form>
  );
}
