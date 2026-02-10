"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/Button";
import type { BookingSlot, Master, Service } from "@/lib/types";

type HomeBookingFormProps = {
  services: Service[];
  masters: Master[];
};

export function HomeBookingForm({ services, masters }: HomeBookingFormProps) {
  const [selectedService, setSelectedService] = useState("");
  const [selectedMaster, setSelectedMaster] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedSlot, setSelectedSlot] = useState("");
  const [slots, setSlots] = useState<BookingSlot[]>([]);
  const [slotsLoaded, setSlotsLoaded] = useState(false);
  const [formSent, setFormSent] = useState(false);

  useEffect(() => {
    const searchParamService = new URLSearchParams(window.location.search).get("service") ?? "";
    setSelectedService(searchParamService);
  }, []);

  const servicesBySlug = useMemo(() => new Map(services.map((service) => [service.slug, service])), [services]);
  const selectedServiceId = servicesBySlug.get(selectedService)?.id ?? null;

  const eligibleMasters = useMemo(() => {
    if (!selectedServiceId) return masters;
    return masters.filter((master) => master.services?.some((service) => service.id === selectedServiceId));
  }, [masters, selectedServiceId]);

  useEffect(() => {
    if (selectedMaster && !eligibleMasters.some((master) => String(master.id) === selectedMaster)) {
      setSelectedMaster("");
    }
  }, [eligibleMasters, selectedMaster]);

  useEffect(() => {
    const fetchSlots = async () => {
      if (!selectedServiceId || !selectedDate) {
        setSlots([]);
        setSlotsLoaded(false);
        return;
      }

      setSelectedSlot("");
      setSlotsLoaded(false);
      try {
        const masterQuery = selectedMaster ? `&master_id=${selectedMaster}` : "";
        const response = await fetch(`/api/public/bookings/slots?service_id=${selectedServiceId}&date=${selectedDate}${masterQuery}`);
        if (!response.ok) {
          setSlots([]);
          setSlotsLoaded(true);
          return;
        }
        const data = (await response.json()) as BookingSlot[];
        setSlots(data);
        setSlotsLoaded(true);
      } catch {
        setSlots([]);
        setSlotsLoaded(true);
      }
    };

    fetchSlots();
  }, [selectedDate, selectedServiceId, selectedMaster]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedServiceId || !selectedSlot) {
      return;
    }

    const formData = new FormData(event.currentTarget);
    const payload = {
      client_name: formData.get("name"),
      client_phone: formData.get("phone"),
      service_id: selectedServiceId,
      master_id: selectedMaster ? Number(selectedMaster) : null,
      starts_at: selectedSlot,
      comment: formData.get("comment")
    };

    try {
      const response = await fetch("/api/public/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        setFormSent(true);
        event.currentTarget.reset();
        setSelectedDate("");
        setSelectedSlot("");
        setSelectedMaster("");
        window.setTimeout(() => setFormSent(false), 4000);
      }
    } catch {
      return;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="text-xs font-medium text-ink-700">Имя</label>
        <input name="name" required className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300" placeholder="Ваше имя" />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Телефон</label>
        <input name="phone" required className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300" placeholder="+7 (___) ___-__-__" />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Услуга</label>
        <select value={selectedService} onChange={(event) => setSelectedService(event.target.value)} className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300">
          <option value="">Выберите услугу</option>
          {services.map((service) => (
            <option key={service.slug} value={service.slug}>{service.title}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Мастер</label>
        <select value={selectedMaster} onChange={(event) => setSelectedMaster(event.target.value)} className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300">
          <option value="">Не важно</option>
          {eligibleMasters.map((master) => (
            <option key={master.id} value={master.id}>{master.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Дата</label>
        <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} required className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300" />
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Время</label>
        <select value={selectedSlot} onChange={(event) => setSelectedSlot(event.target.value)} required className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300">
          <option value="">Выберите время</option>
          {slots.map((slot) => (
            <option key={slot.starts_at} value={slot.starts_at}>{new Date(slot.starts_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}</option>
          ))}
        </select>
        {selectedServiceId && selectedDate && slotsLoaded && slots.length === 0 ? <p className="mt-2 text-xs text-rose-600">Нет доступного времени на выбранную дату. Выберите другую дату.</p> : null}
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Комментарий</label>
        <textarea name="comment" rows={3} className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300" placeholder="Любые пожелания" />
      </div>
      <Button type="submit" className="w-full">Отправить заявку</Button>
      {formSent ? <div className="rounded-2xl bg-blush-50 px-4 py-3 text-center text-xs text-blush-700">Запись принята, мы свяжемся с вами</div> : null}
    </form>
  );
}
