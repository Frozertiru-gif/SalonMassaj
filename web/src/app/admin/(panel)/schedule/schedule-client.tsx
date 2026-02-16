"use client";

import { Fragment, useMemo, useState } from "react";
import type { AdminAvailabilityResponse, AdminScheduleResponse, ScheduleBooking } from "@/lib/types";
import { Card } from "@/components/Card";
import { clientAdminFetch } from "@/lib/clientApi";

const STATUS_OPTIONS = ["NEW", "CONFIRMED", "CANCELLED"];

function timeToMinutes(value: string): number {
  const [h, m] = value.split(":").map(Number);
  return h * 60 + m;
}

function padTime(total: number): string {
  const h = String(Math.floor(total / 60)).padStart(2, "0");
  const m = String(total % 60).padStart(2, "0");
  return `${h}:${m}`;
}

function toIsoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

function displayDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString("ru-RU");
}

type QuickState = {
  date: string;
  time: string;
  master_id?: number;
} | null;

export function ScheduleClient({
  initialDate,
  initialSchedule,
  initialAvailability
}: {
  initialDate: string;
  initialSchedule: AdminScheduleResponse;
  initialAvailability: AdminAvailabilityResponse;
}) {
  const [date, setDate] = useState(initialDate);
  const [mode, setMode] = useState<"day" | "week">("day");
  const [schedule, setSchedule] = useState(initialSchedule);
  const [availability, setAvailability] = useState(initialAvailability);
  const [error, setError] = useState<string | null>(null);
  const [quickState, setQuickState] = useState<QuickState>(null);
  const [searchMasterId, setSearchMasterId] = useState<string>("any");
  const [searchResults, setSearchResults] = useState<Array<{ date: string; time: string; master_id: number; master_name: string }>>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const masters = availability.masters;

  const timeAxis = useMemo(() => {
    const all = Object.values(availability.slots_by_master).flat();
    const min = all.length > 0 ? Math.min(...all.map(timeToMinutes)) : 10 * 60;
    const max = all.length > 0 ? Math.max(...all.map(timeToMinutes)) + availability.service.duration_min : 21 * 60;
    const list: string[] = [];
    for (let cursor = min; cursor <= max; cursor += availability.slot_step_min) {
      list.push(padTime(cursor));
    }
    return list;
  }, [availability]);

  const bookingsByMasterAndTime = useMemo(() => {
    const map = new Map<string, ScheduleBooking>();
    for (const booking of schedule.bookings) {
      if (booking.master_id == null) continue;
      const time = new Date(booking.starts_at).toTimeString().slice(0, 5);
      map.set(`${booking.master_id}-${time}`, booking);
    }
    return map;
  }, [schedule.bookings]);

  const reloadData = async (nextDate: string, nextMode: "day" | "week") => {
    setError(null);
    try {
      const [scheduleRes, availabilityRes] = await Promise.all([
        clientAdminFetch(`/api/admin/schedule?date=${nextDate}&mode=${nextMode}`),
        clientAdminFetch(`/api/admin/availability?date=${nextDate}&service_id=1`)
      ]);

      if (!scheduleRes.ok || !availabilityRes.ok) {
        const detail = (await scheduleRes.json().catch(() => null)) as { detail?: string } | null;
        setError(detail?.detail ?? "Не удалось загрузить расписание");
        return;
      }

      setSchedule((await scheduleRes.json()) as AdminScheduleResponse);
      setAvailability((await availabilityRes.json()) as AdminAvailabilityResponse);
    } catch {
      setError("Ошибка сети при загрузке расписания");
    }
  };

  const handleQuickBooking = async (formData: FormData) => {
    setError(null);
    const payload = {
      client_name: formData.get("client_name") || null,
      client_phone: formData.get("client_phone"),
      service_id: 1,
      master_id: Number(formData.get("master_id")),
      date: formData.get("date"),
      time: formData.get("time"),
      comment: formData.get("comment") || "по телефону",
      status: formData.get("status") || "CONFIRMED"
    };

    try {
      const response = await clientAdminFetch("/api/admin/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const data = (await response.json().catch(() => null)) as { detail?: string } | null;
        setError(data?.detail ?? "Не удалось создать запись");
        return;
      }
      setQuickState(null);
      await reloadData(date, mode);
    } catch {
      setError("Не удалось создать запись");
    }
  };

  const handleFindSlots = async () => {
    setSearchLoading(true);
    setSearchResults([]);
    setError(null);
    try {
      const base = new Date(`${date}T00:00:00`);
      const results: Array<{ date: string; time: string; master_id: number; master_name: string }> = [];
      for (let i = 0; i < 7 && results.length < 20; i += 1) {
        const current = new Date(base);
        current.setDate(base.getDate() + i);
        const day = toIsoDate(current);
        const response = await clientAdminFetch(`/api/admin/availability?date=${day}&service_id=1`);
        if (!response.ok) {
          continue;
        }
        const data = (await response.json()) as AdminAvailabilityResponse;
        for (const master of data.masters) {
          if (searchMasterId !== "any" && Number(searchMasterId) !== master.id) continue;
          const times = data.slots_by_master[String(master.id)] ?? [];
          for (const time of times) {
            results.push({ date: day, time, master_id: master.id, master_name: master.name });
            if (results.length >= 20) break;
          }
          if (results.length >= 20) break;
        }
      }
      setSearchResults(results);
    } catch {
      setError("Не удалось найти ближайшие окна");
    } finally {
      setSearchLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="text-xs text-ink-500">Дата</label>
          <input
            type="date"
            className="mt-1 rounded-xl border border-blush-100 px-3 py-2"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              void reloadData(e.target.value, mode);
            }}
          />
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className={`rounded-full px-4 py-2 text-sm ${mode === "day" ? "bg-blush-200" : "border border-blush-100 bg-white"}`}
            onClick={() => {
              setMode("day");
              void reloadData(date, "day");
            }}
          >
            День
          </button>
          <button
            type="button"
            className={`rounded-full px-4 py-2 text-sm ${mode === "week" ? "bg-blush-200" : "border border-blush-100 bg-white"}`}
            onClick={() => {
              setMode("week");
              void reloadData(date, "week");
            }}
          >
            Неделя
          </button>
        </div>
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <Card className="overflow-auto">
        <div className="min-w-[800px]">
          <div className="grid" style={{ gridTemplateColumns: `120px repeat(${masters.length}, minmax(160px, 1fr))` }}>
            <div className="border-b border-blush-100 p-2 text-xs uppercase text-ink-500">Время</div>
            {masters.map((master) => (
              <div key={master.id} className="border-b border-blush-100 p-2 text-sm font-medium text-ink-900">{master.name}</div>
            ))}
            {timeAxis.map((time) => (
              <Fragment key={time}>
                <div key={`t-${time}`} className="border-b border-blush-50 p-2 text-xs text-ink-500">{time}</div>
                {masters.map((master) => {
                  const booking = bookingsByMasterAndTime.get(`${master.id}-${time}`);
                  const free = (availability.slots_by_master[String(master.id)] ?? []).includes(time);
                  return (
                    <div key={`${master.id}-${time}`} className="border-b border-l border-blush-50 p-1">
                      {booking ? (
                        <div className="rounded-lg bg-blush-100 p-2 text-xs">
                          <p className="font-semibold">{booking.client_name}</p>
                          <p>{booking.client_phone}</p>
                          <p className="uppercase text-[10px]">{booking.status} • {booking.source === "admin" ? "админ" : "публично"}</p>
                        </div>
                      ) : free ? (
                        <button
                          type="button"
                          className="w-full rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs text-emerald-800"
                          onClick={() => setQuickState({ date, time, master_id: master.id })}
                        >
                          + Записать
                        </button>
                      ) : (
                        <div className="h-8 rounded-lg bg-slate-50" />
                      )}
                    </div>
                  );
                })}
              </Fragment>
            ))}
          </div>
        </div>
      </Card>

      <Card className="space-y-3">
        <p className="text-sm font-semibold">Поиск ближайшего окна</p>
        <div className="flex flex-wrap gap-3">
          <select value={searchMasterId} onChange={(e) => setSearchMasterId(e.target.value)} className="rounded-xl border border-blush-100 px-3 py-2 text-sm">
            <option value="any">Любой мастер</option>
            {masters.map((master) => (
              <option key={master.id} value={master.id}>{master.name}</option>
            ))}
          </select>
          <button type="button" className="rounded-full bg-blush-200 px-4 py-2 text-sm" onClick={() => void handleFindSlots()} disabled={searchLoading}>
            {searchLoading ? "Поиск..." : "Найти"}
          </button>
        </div>
        <div className="space-y-1">
          {searchResults.map((item) => (
            <button
              type="button"
              key={`${item.date}-${item.time}-${item.master_id}`}
              className="block w-full rounded-lg border border-blush-100 px-3 py-2 text-left text-sm"
              onClick={() => setQuickState({ date: item.date, time: item.time, master_id: item.master_id })}
            >
              {displayDate(item.date)} {item.time} — {item.master_name}
            </button>
          ))}
          {searchResults.length === 0 && !searchLoading ? <p className="text-xs text-ink-500">Нет результатов</p> : null}
        </div>
      </Card>

      {quickState ? (
        <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/30 p-4">
          <Card className="w-full max-w-lg space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-lg font-semibold">Быстрая запись</p>
                <p className="text-xs text-ink-500">{displayDate(quickState.date)} {quickState.time}</p>
              </div>
              <button type="button" onClick={() => setQuickState(null)}>✕</button>
            </div>
            <form
              className="grid gap-3 md:grid-cols-2"
              onSubmit={async (event) => {
                event.preventDefault();
                await handleQuickBooking(new FormData(event.currentTarget));
              }}
            >
              <input type="hidden" name="date" value={quickState.date} />
              <input type="hidden" name="time" value={quickState.time} />
              <div>
                <label className="text-xs text-ink-500">Телефон</label>
                <input name="client_phone" required className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-ink-500">Имя</label>
                <input name="client_name" className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="text-xs text-ink-500">Мастер</label>
                <select name="master_id" defaultValue={String(quickState.master_id ?? "")} className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm" required>
                  <option value="">Выберите мастера</option>
                  {masters.map((master) => (
                    <option key={master.id} value={master.id}>{master.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-ink-500">Статус</label>
                <select name="status" defaultValue="CONFIRMED" className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm">
                  {STATUS_OPTIONS.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-ink-500">Комментарий</label>
                <textarea name="comment" rows={3} defaultValue="по телефону" className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm" />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <button type="button" onClick={() => setQuickState(null)} className="rounded-full border border-blush-100 px-4 py-2 text-sm">Отмена</button>
                <button type="submit" className="rounded-full bg-blush-200 px-4 py-2 text-sm">Сохранить</button>
              </div>
            </form>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
