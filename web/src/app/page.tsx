"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";
import { ServiceCard } from "@/components/ServiceCard";
import { ReviewCard } from "@/components/ReviewCard";
import { reviews } from "@/data/reviews";
import type { AvailabilitySlot, Service } from "@/lib/types";

const advantages = [
  { title: "Персональные ритуалы", text: "Подбираем технику и масла под ваше состояние.", icon: "🌸" },
  { title: "Премиальные материалы", text: "Органические масла и тёплые текстуры.", icon: "🕯️" },
  { title: "Спокойная атмосфера", text: "Тишина, мягкий свет и ароматерапия.", icon: "✨" },
  { title: "Внимание к деталям", text: "Комфорт с первого касания и до финального чая.", icon: "🤍" }
];

export default function HomePage() {
  const searchParams = useSearchParams();
  const initialService = searchParams.get("service") ?? "";
  const [services, setServices] = useState<Service[]>([]);
  const [contacts, setContacts] = useState({ phone: "+7 (999) 123-45-67", address: "Москва, ул. Пудровая, 12" });
  const [selectedService, setSelectedService] = useState<string>(initialService);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedSlot, setSelectedSlot] = useState<string>("");
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [formSent, setFormSent] = useState(false);

  const servicesPreview = useMemo(() => services.slice(0, 8), [services]);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch("/api/public/services");
        if (!response.ok) {
          setServices([]);
          return;
        }
        const data = (await response.json()) as Service[];
        setServices(data);
      } catch (error) {
        setServices([]);
      }
    };
    const fetchContacts = async () => {
      try {
        const response = await fetch("/api/public/settings/contacts");
        if (!response.ok) {
          return;
        }
        const data = (await response.json()) as { value_jsonb: { phone?: string; address?: string } };
        setContacts((prev) => ({
          phone: data.value_jsonb.phone ?? prev.phone,
          address: data.value_jsonb.address ?? prev.address
        }));
      } catch (error) {
        return;
      }
    };
    fetchServices();
    fetchContacts();
  }, []);

  useEffect(() => {
    const match = services.find((service) => service.slug === selectedService);
    setSelectedServiceId(match?.id ?? null);
  }, [selectedService, services]);

  useEffect(() => {
    const fetchSlots = async () => {
      if (!selectedServiceId || !selectedDate) {
        setSlots([]);
        return;
      }
      setSelectedSlot("");
      try {
        const response = await fetch(
          `/api/public/availability?service_id=${selectedServiceId}&date=${selectedDate}`
        );
        if (!response.ok) {
          setSlots([]);
          return;
        }
        const data = (await response.json()) as { slots: AvailabilitySlot[] };
        setSlots(data.slots);
      } catch (error) {
        setSlots([]);
      }
    };
    fetchSlots();
  }, [selectedServiceId, selectedDate]);

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
        setTimeout(() => setFormSent(false), 4000);
      }
    } catch (error) {
      return;
    }
  };

  return (
    <div>
      <Section className="pt-12">
        <Container className="grid items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Премиальный массажный салон</p>
            <h1 className="text-4xl font-semibold leading-tight text-ink-900 sm:text-5xl">
              Нежный уход для тела и разума в пастельной эстетике
            </h1>
            <p className="text-base text-ink-700">
              Погрузитесь в атмосферу спокойствия и заботы: мягкие ритуалы, тёплые масла и индивидуальные программы для
              восстановления энергии.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button href="#booking">Записаться</Button>
              <Button href="/services" variant="secondary">
                Услуги
              </Button>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-ink-700">
              <span>⏳ 60–90 мин</span>
              <span>🌿 Натуральные масла</span>
              <span>☕ Чайная церемония после сеанса</span>
            </div>
          </div>
          <div className="relative">
            <div className="absolute -left-6 -top-6 h-full w-full rounded-3xl bg-gradient-to-br from-blush-100 via-blush-50 to-white" />
            <div className="relative rounded-3xl bg-white/80 p-8 shadow-soft ring-1 ring-blush-100">
              <div className="space-y-4">
                <p className="text-sm uppercase tracking-[0.2em] text-blush-500">Ритуал недели</p>
                <h2 className="text-2xl font-semibold text-ink-900">Арома-релакс массаж</h2>
                <p className="text-sm text-ink-700">
                  Тёплые масла, спокойный свет и плавные движения для глубокого расслабления.
                </p>
                <Button href="/services/aroma-relax" variant="ghost">
                  Подробнее →
                </Button>
              </div>
            </div>
          </div>
        </Container>
      </Section>

      <Section>
        <Container>
          <div className="flex items-end justify-between gap-6">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Каталог услуг</p>
              <h2 className="mt-3 text-3xl font-semibold text-ink-900">Выберите свой ритуал</h2>
            </div>
            <Button href="/services" variant="ghost" className="hidden sm:inline-flex">
              Смотреть все →
            </Button>
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {servicesPreview.map((service) => (
              <ServiceCard key={service.slug} service={service} />
            ))}
          </div>
        </Container>
      </Section>

      <Section className="bg-gradient-to-br from-blush-50 via-white to-blush-100">
        <Container>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {advantages.map((item) => (
              <Card key={item.title}>
                <div className="text-2xl">{item.icon}</div>
                <h3 className="mt-4 text-lg font-semibold text-ink-900">{item.title}</h3>
                <p className="mt-2 text-sm text-ink-700">{item.text}</p>
              </Card>
            ))}
          </div>
        </Container>
      </Section>

      <Section id="about">
        <Container className="grid items-center gap-10 lg:grid-cols-[1fr_1fr]">
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">О нас</p>
            <h2 className="text-3xl font-semibold text-ink-900">Пространство, где забота ощущается в каждой детали</h2>
            <p className="text-base text-ink-700">
              Мы создали салон, в котором можно выдохнуть и довериться профессионалам. Наши мастера работают бережно,
              подбирают техники и уделяют внимание вашему состоянию.
            </p>
            <p className="text-base text-ink-700">
              В интерьере — мягкий текстиль, пастельные оттенки и тихая музыка. В конце сеанса мы предлагаем тёплый чай,
              чтобы зафиксировать ощущение спокойствия.
            </p>
          </div>
          <div className="relative">
            <div className="absolute -left-6 -top-6 h-full w-full rounded-3xl bg-gradient-to-br from-blush-200 via-blush-100 to-white" />
            <div className="relative h-80 rounded-3xl bg-white/80 shadow-soft ring-1 ring-blush-100">
              <div className="flex h-full items-center justify-center text-sm text-blush-500">
                Фото салона (плейсхолдер)
              </div>
            </div>
          </div>
        </Container>
      </Section>

      <Section id="reviews" className="bg-white/70">
        <Container>
          <div className="flex flex-col gap-3">
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Отзывы</p>
            <h2 className="text-3xl font-semibold text-ink-900">Гости рассказывают о своих ощущениях</h2>
          </div>
          <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {reviews.map((review) => (
              <ReviewCard key={review.name} review={review} />
            ))}
          </div>
        </Container>
      </Section>

      <Section id="booking">
        <Container className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Запись</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink-900">Запланируйте визит</h2>
            <p className="mt-4 text-base text-ink-700">
              Оставьте заявку, и мы свяжемся с вами, чтобы подобрать удобное время. Ответим в течение 15 минут в рабочее
              время.
            </p>
            <div className="mt-6 space-y-3 text-sm text-ink-700">
              <p>📞 {contacts.phone}</p>
              <p>📍 {contacts.address}</p>
              <p>🕒 Ежедневно 10:00–21:00</p>
            </div>
          </div>
          <Card>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-ink-700">Имя</label>
                <input
                  name="name"
                  required
                  className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300"
                  placeholder="Ваше имя"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-ink-700">Телефон</label>
                <input
                  name="phone"
                  required
                  className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300"
                  placeholder="+7 (___) ___-__-__"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-ink-700">Услуга</label>
                <select
                  value={selectedService}
                  onChange={(event) => setSelectedService(event.target.value)}
                  className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300"
                >
                  <option value="">Выберите услугу</option>
                  {services.map((service) => (
                    <option key={service.slug} value={service.slug}>
                      {service.title}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-ink-700">Дата</label>
                <input
                  type="date"
                  value={selectedDate}
                  onChange={(event) => setSelectedDate(event.target.value)}
                  required
                  className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-ink-700">Время</label>
                <select
                  value={selectedSlot}
                  onChange={(event) => setSelectedSlot(event.target.value)}
                  required
                  className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300"
                >
                  <option value="">Выберите время</option>
                  {slots.map((slot) => (
                    <option key={slot.starts_at} value={slot.starts_at}>
                      {new Date(slot.starts_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs font-medium text-ink-700">Комментарий</label>
                <textarea
                  name="comment"
                  rows={3}
                  className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900 outline-none transition focus:border-blush-300"
                  placeholder="Любые пожелания"
                />
              </div>
              <Button type="submit" className="w-full">
                Отправить заявку
              </Button>
              {formSent ? (
                <div className="rounded-2xl bg-blush-50 px-4 py-3 text-center text-xs text-blush-700">
                  Запись принята, мы свяжемся с вами
                </div>
              ) : null}
            </form>
          </Card>
        </Container>
      </Section>
    </div>
  );
}
