"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { BookingSlot, Service } from "@/lib/types";
import { clientAdminFetch } from "@/lib/clientApi";

const STATUS_OPTIONS = ["NEW", "CONFIRMED", "CANCELLED", "DONE"] as const;

export function AdminBookingCreateForm({ services }: { services: Service[] }) {
  const router = useRouter();
  const [serviceId, setServiceId] = useState<string>("");
  const [date, setDate] = useState<string>("");
  const [time, setTime] = useState<string>("");
  const [slots, setSlots] = useState<BookingSlot[]>([]);
  const [slotsLoaded, setSlotsLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const loadSlots = async () => {
      if (!serviceId || !date) {
        setSlots([]);
        setSlotsLoaded(false);
        return;
      }
      setTime("");
      setSlotsLoaded(false);
      const response = await fetch(`/api/public/bookings/slots?service_id=${serviceId}&date=${date}`);
      if (!response.ok) {
        setSlots([]);
        setSlotsLoaded(true);
        return;
      }
      const data = (await response.json()) as BookingSlot[];
      setSlots(data);
      setSlotsLoaded(true);
    };

    loadSlots().catch(() => {
      setSlots([]);
      setSlotsLoaded(true);
    });
  }, [serviceId, date]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    const formData = new FormData(event.currentTarget);
    const payload = {
      client_name: formData.get("client_name") || null,
      client_phone: formData.get("client_phone"),
      service_id: Number(formData.get("service_id")),
      date: formData.get("date"),
      time: formData.get("time"),
      comment: formData.get("comment") || null,
      status: formData.get("status")
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

      setSuccess("Запись создана");
      event.currentTarget.reset();
      setServiceId("");
      setDate("");
      setTime("");
      setSlots([]);
      setSlotsLoaded(false);
      router.refresh();
    } catch {
      setError("Не удалось создать запись");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="grid gap-3 md:grid-cols-2">
      <div>
        <label className="text-xs font-medium text-ink-700">Телефон</label>
        <input name="client_phone" required className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm" />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Имя</label>
        <input name="client_name" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm" />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Услуга</label>
        <select name="service_id" required value={serviceId} onChange={(e) => setServiceId(e.target.value)} className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm">
          <option value="">Выберите услугу</option>
          {services.map((service) => (
            <option key={service.id} value={service.id}>{service.title}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Дата</label>
        <input type="date" name="date" required value={date} onChange={(e) => setDate(e.target.value)} className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm" />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Время</label>
        <select name="time" required value={time} onChange={(e) => setTime(e.target.value)} className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm">
          <option value="">Выберите время</option>
          {slots.map((slot) => (
            <option key={slot.starts_at} value={slot.time}>{slot.time}</option>
          ))}
        </select>
        {serviceId && date && slotsLoaded && slots.length === 0 ? <p className="mt-2 text-xs text-rose-600">Нет доступного времени на выбранную дату.</p> : null}
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Статус</label>
        <select name="status" defaultValue="NEW" className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm">
          {STATUS_OPTIONS.map((status) => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
      </div>
      <div className="md:col-span-2">
        <label className="text-xs font-medium text-ink-700">Комментарий</label>
        <textarea name="comment" rows={3} className="mt-2 w-full rounded-2xl border border-blush-100 px-4 py-3 text-sm" />
      </div>
      <div className="md:col-span-2 flex items-center gap-3">
        <button type="submit" disabled={isSubmitting} className="rounded-full bg-blush-200 px-5 py-2 text-sm font-medium text-ink-900 transition hover:bg-blush-300 disabled:cursor-not-allowed disabled:opacity-60">{isSubmitting ? "Создание..." : "Создать"}</button>
        {success ? <p className="text-xs text-emerald-700">{success}</p> : null}
        {error ? <p className="text-xs text-rose-600">{error}</p> : null}
      </div>
    </form>
  );
}
