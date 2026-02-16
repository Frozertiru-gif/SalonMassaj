"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import type { AdminAvailabilityResponse, AdminScheduleResponse, ScheduleBooking } from "@/lib/types";
import { Card } from "@/components/Card";
import { AdminToolbar } from "@/components/admin/AdminToolbar";
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

function getWeekDays(anchorDate: string): string[] {
  const date = new Date(`${anchorDate}T00:00:00`);
  const day = date.getDay();
  const shift = day === 0 ? -6 : 1 - day;
  const monday = new Date(date);
  monday.setDate(date.getDate() + shift);

  return Array.from({ length: 7 }, (_, index) => {
    const current = new Date(monday);
    current.setDate(monday.getDate() + index);
    return toIsoDate(current);
  });
}

function bookingDateTimeParts(startsAt: string): { date: string; time: string } {
  const [datePart, timePart] = startsAt.split("T");
  if (datePart && timePart) {
    return { date: datePart, time: timePart.slice(0, 5) };
  }

  const parsed = new Date(startsAt);
  return {
    date: toIsoDate(parsed),
    time: parsed.toTimeString().slice(0, 5)
  };
}

function weekDayHeader(date: string): string {
  return new Date(`${date}T00:00:00`).toLocaleDateString("ru-RU", {
    weekday: "short",
    day: "2-digit",
    month: "2-digit"
  });
}

type QuickState = {
  date: string;
  time: string;
  master_id?: number;
} | null;

function BookingCard({ booking }: { booking: ScheduleBooking }) {
  return (
    <div className="rounded-lg bg-blush-100 p-2 text-xs">
      <p className="font-semibold">{booking.client_name}</p>
      <p>{booking.client_phone}</p>
      <p className="uppercase text-[10px]">{booking.status} • {booking.source === "admin" ? "админ" : "публично"}</p>
    </div>
  );
}

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
  const [weekMasterId, setWeekMasterId] = useState<string>(String(initialAvailability.masters[0]?.id ?? ""));
  const [dayMasterId, setDayMasterId] = useState<string>(String(initialAvailability.masters[0]?.id ?? ""));
  const [searchMasterId, setSearchMasterId] = useState<string>("any");
  const [searchResults, setSearchResults] = useState<Array<{ date: string; time: string; master_id: number; master_name: string }>>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const masters = availability.masters;

  useEffect(() => {
    if (masters.length === 0) {
      setWeekMasterId("");
      setDayMasterId("");
      return;
    }

    if (!masters.some((master) => String(master.id) === weekMasterId)) {
      setWeekMasterId(String(masters[0].id));
    }

    if (!masters.some((master) => String(master.id) === dayMasterId)) {
      setDayMasterId(String(masters[0].id));
    }
  }, [masters, weekMasterId, dayMasterId]);

  const selectedWeekMaster = masters.find((master) => String(master.id) === weekMasterId) ?? null;
  const selectedDayMaster = masters.find((master) => String(master.id) === dayMasterId) ?? null;
  const weekDays = useMemo(() => getWeekDays(date), [date]);

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

  const bookingsBySlot = useMemo(() => {
    const map = new Map<string, ScheduleBooking>();
    for (const booking of schedule.bookings) {
      if (booking.master_id == null) continue;
      const { date: bookingDate, time } = bookingDateTimeParts(booking.starts_at);
      map.set(`${bookingDate}|${time}|${booking.master_id}`, booking);
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

  const mobileActionCandidate = useMemo(() => {
    const targetMaster = mode === "day" ? selectedDayMaster : selectedWeekMaster;
    if (!targetMaster) return null;
    const slots = availability.slots_by_master[String(targetMaster.id)] ?? [];
    if (slots.length === 0) return null;
    return {
      date,
      time: slots[0],
      master_id: targetMaster.id
    };
  }, [availability.slots_by_master, date, mode, selectedDayMaster, selectedWeekMaster]);

  return (
    <div className="space-y-4 pb-16 md:pb-0">
      <AdminToolbar stickyMobile>
        <div>
          <label className="text-xs text-ink-500">Дата</label>
          <input
            type="date"
            className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 md:min-w-[180px]"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              void reloadData(e.target.value, mode);
            }}
          />
        </div>
        <div className="grid grid-cols-2 gap-2 rounded-full bg-blush-50 p-1">
          <button
            type="button"
            className={`rounded-full px-4 py-2 text-sm ${mode === "day" ? "bg-blush-200" : "bg-white"}`}
            onClick={() => {
              setMode("day");
              void reloadData(date, "day");
            }}
          >
            День
          </button>
          <button
            type="button"
            className={`rounded-full px-4 py-2 text-sm ${mode === "week" ? "bg-blush-200" : "bg-white"}`}
            onClick={() => {
              setMode("week");
              void reloadData(date, "week");
            }}
          >
            Неделя
          </button>
        </div>
        <div className="w-full md:w-auto">
          <label className="text-xs text-ink-500">Мастер</label>
          <select
            className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm md:min-w-[220px]"
            value={mode === "week" ? weekMasterId : dayMasterId}
            onChange={(event) => {
              if (mode === "week") {
                setWeekMasterId(event.target.value);
              } else {
                setDayMasterId(event.target.value);
              }
            }}
          >
            {masters.map((master) => (
              <option key={master.id} value={master.id}>
                {master.name}
              </option>
            ))}
          </select>
        </div>
      </AdminToolbar>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <div className="hidden md:block">
        {mode === "day" ? (
          <Card className="overflow-x-auto">
            <div className="min-w-[800px]">
              <div className="grid" style={{ gridTemplateColumns: `120px repeat(${masters.length}, minmax(160px, 1fr))` }}>
                <div className="border-b border-blush-100 p-2 text-xs uppercase text-ink-500">Время</div>
                {masters.map((master) => (
                  <div key={master.id} className="border-b border-blush-100 p-2 text-sm font-medium text-ink-900">
                    {master.name}
                  </div>
                ))}
                {timeAxis.map((time) => (
                  <Fragment key={time}>
                    <div className="border-b border-blush-50 p-2 text-xs text-ink-500">{time}</div>
                    {masters.map((master) => {
                      const booking = bookingsBySlot.get(`${date}|${time}|${master.id}`);
                      const free = (availability.slots_by_master[String(master.id)] ?? []).includes(time);
                      return (
                        <div key={`${master.id}-${time}`} className="border-b border-l border-blush-50 p-1">
                          {booking ? (
                            <BookingCard booking={booking} />
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
        ) : (
          <Card className="overflow-x-auto">
            <div className="min-w-[980px]">
              <div className="grid" style={{ gridTemplateColumns: "120px repeat(7, minmax(130px, 1fr))" }}>
                <div className="sticky left-0 top-0 z-30 border-b border-blush-100 bg-white p-2 text-xs uppercase text-ink-500">Время</div>
                {weekDays.map((day) => (
                  <div key={day} className="sticky top-0 z-20 border-b border-l border-blush-100 bg-white p-2 text-xs font-semibold uppercase text-ink-900">
                    {weekDayHeader(day)}
                  </div>
                ))}
                {timeAxis.map((time) => (
                  <Fragment key={time}>
                    <div className="sticky left-0 z-10 border-b border-blush-50 bg-white p-2 text-xs text-ink-500">{time}</div>
                    {weekDays.map((day) => {
                      const booking = selectedWeekMaster ? bookingsBySlot.get(`${day}|${time}|${selectedWeekMaster.id}`) : undefined;
                      return (
                        <div key={`${day}-${time}`} className="border-b border-l border-blush-50 p-1">
                          {booking ? (
                            <BookingCard booking={booking} />
                          ) : selectedWeekMaster ? (
                            <button
                              type="button"
                              className="w-full rounded-lg border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs text-emerald-800"
                              onClick={() => setQuickState({ date: day, time, master_id: selectedWeekMaster.id })}
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
        )}
      </div>

      <div className="space-y-3 md:hidden">
        {mode === "day" ? (
          <Card className="space-y-3">
            <p className="text-sm font-semibold text-ink-900">{selectedDayMaster?.name ?? "Выберите мастера"}</p>
            <div className="space-y-2">
              {timeAxis.map((time) => {
                const masterId = selectedDayMaster?.id;
                const booking = masterId ? bookingsBySlot.get(`${date}|${time}|${masterId}`) : undefined;
                const free = masterId ? (availability.slots_by_master[String(masterId)] ?? []).includes(time) : false;
                return (
                  <div key={time} className="rounded-xl border border-blush-100 bg-white p-2">
                    <p className="text-xs font-semibold text-ink-500">{time}</p>
                    <div className="mt-1">
                      {booking ? (
                        <BookingCard booking={booking} />
                      ) : free && masterId ? (
                        <button
                          type="button"
                          className="w-full rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
                          onClick={() => setQuickState({ date, time, master_id: masterId })}
                        >
                          Записать
                        </button>
                      ) : (
                        <p className="text-xs text-ink-400">Свободных окон нет</p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        ) : (
          <div className="space-y-2">
            {weekDays.map((day) => (
              <details key={day} className="rounded-2xl border border-blush-100 bg-white p-3" open={day === date}>
                <summary className="cursor-pointer text-sm font-semibold text-ink-900">{weekDayHeader(day)}</summary>
                <div className="mt-3 space-y-2">
                  {timeAxis.map((time) => {
                    const masterId = selectedWeekMaster?.id;
                    const booking = masterId ? bookingsBySlot.get(`${day}|${time}|${masterId}`) : undefined;
                    const free = masterId ? (availability.slots_by_master[String(masterId)] ?? []).includes(time) : false;
                    return (
                      <div key={`${day}-${time}`} className="rounded-xl border border-blush-100 p-2">
                        <p className="text-xs font-semibold text-ink-500">{time}</p>
                        <div className="mt-1">
                          {booking ? (
                            <BookingCard booking={booking} />
                          ) : free && masterId ? (
                            <button
                              type="button"
                              className="w-full rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800"
                              onClick={() => setQuickState({ date: day, time, master_id: masterId })}
                            >
                              Записать
                            </button>
                          ) : (
                            <p className="text-xs text-ink-400">Свободных окон нет</p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </details>
            ))}
          </div>
        )}
      </div>

      <Card className="space-y-3">
        <p className="text-sm font-semibold">Поиск ближайшего окна</p>
        <div className="flex flex-col gap-3 md:flex-row md:flex-wrap">
          <select value={searchMasterId} onChange={(e) => setSearchMasterId(e.target.value)} className="rounded-xl border border-blush-100 px-3 py-2 text-sm">
            <option value="any">Любой мастер</option>
            {masters.map((master) => (
              <option key={master.id} value={master.id}>
                {master.name}
              </option>
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

      {mobileActionCandidate ? (
        <button
          type="button"
          className="fixed bottom-4 right-4 z-30 rounded-full bg-blush-500 px-4 py-3 text-sm font-medium text-white shadow-lg md:hidden"
          onClick={() => setQuickState(mobileActionCandidate)}
        >
          + Запись
        </button>
      ) : null}

      {quickState ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 p-4">
          <Card className="w-full max-w-lg space-y-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-lg font-semibold">Быстрая запись</p>
                <p className="text-xs text-ink-500">
                  {displayDate(quickState.date)} {quickState.time}
                </p>
              </div>
              <button type="button" onClick={() => setQuickState(null)}>
                ✕
              </button>
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
                    <option key={master.id} value={master.id}>
                      {master.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-ink-500">Статус</label>
                <select name="status" defaultValue="CONFIRMED" className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm">
                  {STATUS_OPTIONS.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-xs text-ink-500">Комментарий</label>
                <textarea name="comment" rows={3} defaultValue="по телефону" className="mt-1 w-full rounded-xl border border-blush-100 px-3 py-2 text-sm" />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <button type="button" onClick={() => setQuickState(null)} className="rounded-full border border-blush-100 px-4 py-2 text-sm">
                  Отмена
                </button>
                <button type="submit" className="rounded-full bg-blush-200 px-4 py-2 text-sm">
                  Сохранить
                </button>
              </div>
            </form>
          </Card>
        </div>
      ) : null}
    </div>
  );
}
