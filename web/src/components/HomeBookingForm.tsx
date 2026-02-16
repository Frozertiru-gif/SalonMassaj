"use client";

import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/Button";
import type { BookingSlot, Master, Service } from "@/lib/types";

const ANY_MASTER_VALUE = "__any__";
const DEFAULT_BOOKING_RULES = {
  min_lead_min: 0,
  max_days_ahead: 60
};
const DEFAULT_SLOT_STEP_MIN = 30;
const PLACEHOLDER_MASTER_NAMES = new Set(["не важно", "неважно", "любой", "любой мастер", "any"]);
const PLACEHOLDER_MASTER_SLUGS = new Set(["any", "any-master", "ne-vazhno", "nevazhno"]);

type BookingRules = {
  min_lead_min: number;
  max_days_ahead: number;
};

type PublicSettingResponse = {
  key: string;
  value_jsonb: unknown;
};

type HomeBookingFormProps = {
  services: Service[];
  masters: Master[];
};

const isBookingRules = (value: unknown): value is BookingRules => {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Partial<BookingRules>;
  return typeof candidate.min_lead_min === "number" && typeof candidate.max_days_ahead === "number";
};

const formatDateInputValue = (date: Date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const formatDatePretty = (value: string) => {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) {
    return value;
  }
  return new Date(year, month - 1, day).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric"
  });
};

const isPlaceholderMaster = (master: Master) => {
  const normalizedName = master.name.trim().toLowerCase();
  const normalizedSlug = master.slug.trim().toLowerCase();
  return PLACEHOLDER_MASTER_NAMES.has(normalizedName) || PLACEHOLDER_MASTER_SLUGS.has(normalizedSlug);
};

export function HomeBookingForm({ services, masters }: HomeBookingFormProps) {
  const [selectedService, setSelectedService] = useState("");
  const [selectedMaster, setSelectedMaster] = useState(ANY_MASTER_VALUE);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedSlot, setSelectedSlot] = useState("");
  const [slots, setSlots] = useState<BookingSlot[]>([]);
  const [slotsLoaded, setSlotsLoaded] = useState(false);
  const [formSent, setFormSent] = useState(false);
  const [bookingRules, setBookingRules] = useState<BookingRules>(DEFAULT_BOOKING_RULES);
  const [slotStepMin, setSlotStepMin] = useState(DEFAULT_SLOT_STEP_MIN);

  useEffect(() => {
    const searchParamService = new URLSearchParams(window.location.search).get("service") ?? "";
    setSelectedService(searchParamService);
  }, []);

  useEffect(() => {
    const loadPublicSettings = async () => {
      try {
        const [bookingRulesResponse, slotStepResponse] = await Promise.all([
          fetch("/api/public/settings/booking_rules"),
          fetch("/api/public/settings/slot_step_min")
        ]);

        if (bookingRulesResponse.ok) {
          const bookingRulesData = (await bookingRulesResponse.json()) as PublicSettingResponse;
          if (isBookingRules(bookingRulesData.value_jsonb)) {
            setBookingRules(bookingRulesData.value_jsonb);
          }
        }

        if (slotStepResponse.ok) {
          const slotStepData = (await slotStepResponse.json()) as PublicSettingResponse;
          if (typeof slotStepData.value_jsonb === "number") {
            setSlotStepMin(slotStepData.value_jsonb);
          }
        }
      } catch {
        return;
      }
    };

    loadPublicSettings();
  }, []);

  const servicesBySlug = useMemo(() => new Map(services.map((service) => [service.slug, service])), [services]);
  const selectedServiceId = servicesBySlug.get(selectedService)?.id ?? null;
  const today = useMemo(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    return now;
  }, []);
  const minDate = useMemo(() => formatDateInputValue(today), [today]);
  const maxDate = useMemo(() => {
    const limit = new Date(today);
    limit.setDate(limit.getDate() + bookingRules.max_days_ahead);
    return formatDateInputValue(limit);
  }, [bookingRules.max_days_ahead, today]);
  const selectedDateTooFar = selectedDate ? selectedDate > maxDate : false;
  const selectedDateBeforeMin = selectedDate ? selectedDate < minDate : false;
  const selectedDateOutOfRange = selectedDateTooFar || selectedDateBeforeMin;

  const normalizedMasters = useMemo(() => masters.filter((master) => !isPlaceholderMaster(master)), [masters]);

  const eligibleMasters = useMemo(() => {
    if (!selectedServiceId) return normalizedMasters;
    return normalizedMasters.filter((master) => master.services?.some((service) => service.id === selectedServiceId));
  }, [normalizedMasters, selectedServiceId]);

  useEffect(() => {
    if (selectedMaster === ANY_MASTER_VALUE) {
      return;
    }
    if (!eligibleMasters.some((master) => String(master.id) === selectedMaster)) {
      setSelectedMaster(ANY_MASTER_VALUE);
    }
  }, [eligibleMasters, selectedMaster]);

  useEffect(() => {
    const fetchSlots = async () => {
      if (!selectedServiceId || !selectedDate || selectedDateOutOfRange) {
        setSlots([]);
        setSlotsLoaded(false);
        if (process.env.NODE_ENV !== "production" && selectedDateOutOfRange) {
          console.debug("[booking] slots skipped", {
            mode: selectedMaster === ANY_MASTER_VALUE ? "any" : `master:${selectedMaster}`,
            reason: "too_far"
          });
        }
        return;
      }

      setSelectedSlot("");
      setSlotsLoaded(false);
      try {
        const params = new URLSearchParams({
          service_id: String(selectedServiceId),
          date: selectedDate
        });

        if (selectedMaster !== ANY_MASTER_VALUE) {
          params.set("master_id", selectedMaster);
        }

        const slotsUrl = `/api/public/bookings/slots?${params.toString()}`;
        if (process.env.NODE_ENV !== "production") {
          console.debug("[booking] slots request", {
            mode: selectedMaster === ANY_MASTER_VALUE ? "any" : `master:${selectedMaster}`,
            url: slotsUrl
          });
        }

        const response = await fetch(slotsUrl);
        if (!response.ok) {
          setSlots([]);
          setSlotsLoaded(true);
          return;
        }
        const data = (await response.json()) as BookingSlot[];
        setSlots(data);
        setSlotsLoaded(true);
        if (process.env.NODE_ENV !== "production") {
          console.debug("[booking] slots response", {
            count: data.length,
            reason: data.length === 0 ? "no_slots" : null
          });
        }
      } catch {
        setSlots([]);
        setSlotsLoaded(true);
      }
    };

    fetchSlots();
  }, [selectedDate, selectedDateOutOfRange, selectedServiceId, selectedMaster]);

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
      master_id: selectedMaster === ANY_MASTER_VALUE ? null : Number(selectedMaster),
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
        setSelectedMaster(ANY_MASTER_VALUE);
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
          <option value={ANY_MASTER_VALUE}>Не важно</option>
          {eligibleMasters.map((master) => (
            <option key={master.id} value={master.id}>{master.name}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Дата</label>
        <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} min={minDate} max={maxDate} required className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300" />
        {selectedDateTooFar ? (
          <p className="mt-2 text-xs text-rose-600">Запись доступна только на {bookingRules.max_days_ahead} дней вперёд. Выберите дату до {formatDatePretty(maxDate)}.</p>
        ) : null}
      </div>
      <div>
        <label className="text-xs font-medium text-ink-700">Время</label>
        <select value={selectedSlot} onChange={(event) => setSelectedSlot(event.target.value)} required className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300">
          <option value="">Выберите время</option>
          {slots.map((slot) => (
            <option key={slot.starts_at} value={slot.starts_at}>{new Date(slot.starts_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}</option>
          ))}
        </select>
        <p className="mt-2 text-[11px] text-ink-500">Шаг слотов: {slotStepMin} мин.</p>
        {selectedServiceId && selectedDate && !selectedDateOutOfRange && slotsLoaded && slots.length === 0 ? <p className="mt-2 text-xs text-rose-600">Нет доступного времени на выбранную дату. Выберите другую дату.</p> : null}
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
