"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";
import { ServiceCard } from "@/components/ServiceCard";
import { ReviewCard } from "@/components/ReviewCard";
import { WeeklyRitualCarousel } from "@/components/WeeklyRitualCarousel";
import type { BookingSlot, Review, Service, WeeklyRitual } from "@/lib/types";

const slimfoxHighlights = [
  {
    title: "Сила, которая выглядит нежно",
    text: "Собираем программу так, чтобы вы чувствовали лёгкость и уверенность в каждом движении.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path
          d="M4.5 12.5c2-2 3-5.2 3.3-7l2.2 3 2.2-3c.3 1.8 1.3 5 3.3 7 1.8 1.8 3.5 3.6 3.5 6 0 3-2.4 4.8-7.2 4.8s-7.2-1.8-7.2-4.8c0-2.4 1.7-4.2 3.9-6Z"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    )
  },
  {
    title: "Синтез методик",
    text: "Аппаратные решения, ручные техники и эстетика тела работают как единая система.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M4 12h16M12 4v16" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 7l10 10M17 7l-10 10" strokeLinecap="round" strokeLinejoin="round" opacity="0.3" />
      </svg>
    )
  },
  {
    title: "Персональная траектория",
    text: "Мы видим личность, а не цифры. Всё строится вокруг вашего ритма и целей.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M4 18c2-4 6-7 10-7 2.8 0 4.4 1.2 6 3" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 7a3 3 0 1 1 6 0 3 3 0 0 1-6 0Z" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  },
  {
    title: "Эстетика деталей",
    text: "Пастель, тёплый свет и забота о каждом шаге — для ощущения премиальности.",
    icon: (
      <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M12 4v4M4 12h4M12 20v-4M20 12h-4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M7 7l2 2M17 7l-2 2M7 17l2-2M17 17l-2-2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }
];

export default function HomePage() {
  const searchParams = useSearchParams();
  const initialService = searchParams.get("service") ?? "";
  const [services, setServices] = useState<Service[]>([]);
  const [weeklyRituals, setWeeklyRituals] = useState<WeeklyRitual[]>([]);
  const [publicReviews, setPublicReviews] = useState<Review[]>([]);
  const [contacts, setContacts] = useState({ phone: "+7 (999) 123-45-67", address: "Москва, ул. Пудровая, 12" });
  const [selectedService, setSelectedService] = useState<string>(initialService);
  const [selectedServiceId, setSelectedServiceId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [selectedSlot, setSelectedSlot] = useState<string>("");
  const [slots, setSlots] = useState<BookingSlot[]>([]);
  const [slotsLoaded, setSlotsLoaded] = useState(false);
  const [formSent, setFormSent] = useState(false);

  const servicesPreview = useMemo(() => services.slice(0, 12), [services]);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await fetch("/api/public/services");
        if (!response.ok) {
          setServices([]);
          return;
        }
        const data = (await response.json()) as unknown;
        if (Array.isArray(data)) {
          setServices(data as Service[]);
        } else {
          if (process.env.NODE_ENV !== "production") {
            console.warn("Unexpected services response shape", data);
          }
          setServices([]);
        }
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
    const fetchWeeklyRituals = async () => {
      try {
        const response = await fetch("/api/public/weekly-rituals");
        if (!response.ok) {
          setWeeklyRituals([]);
          return;
        }
        const data = (await response.json()) as WeeklyRitual[];
        setWeeklyRituals(data);
      } catch (error) {
        console.error("Failed to load weekly rituals", error);
        setWeeklyRituals([]);
      }
    };
    const fetchReviews = async () => {
      try {
        const response = await fetch("/api/public/reviews");
        if (!response.ok) {
          setPublicReviews([]);
          return;
        }
        const data = (await response.json()) as Review[];
        setPublicReviews(data);
      } catch (error) {
        console.error("Failed to load reviews", error);
        setPublicReviews([]);
      }
    };
    fetchServices();
    fetchContacts();
    fetchWeeklyRituals();
    fetchReviews();
  }, []);

  useEffect(() => {
    const match = services.find((service) => service.slug === selectedService);
    setSelectedServiceId(match?.id ?? null);
  }, [selectedService, services]);

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
        const response = await fetch(
          `/api/public/bookings/slots?service_id=${selectedServiceId}&date=${selectedDate}`
        );
        if (!response.ok) {
          setSlots([]);
          setSlotsLoaded(true);
          return;
        }
        const data = (await response.json()) as BookingSlot[];
        setSlots(data);
        setSlotsLoaded(true);
      } catch (error) {
        setSlots([]);
        setSlotsLoaded(true);
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
      <Section className="bg-gradient-to-br from-blush-100 via-blush-50 to-peach-100 pt-12">
        <Container className="grid items-center gap-12 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="relative space-y-6">
            <div className="absolute -left-10 -top-8 hidden h-40 w-40 text-blush-200/60 lg:block">
              <svg viewBox="0 0 200 200" fill="none" className="h-full w-full">
                <path
                  d="M40 110c16-16 24-42 26-58l24 26 24-26c2 16 10 42 26 58 14 14 28 30 28 50 0 28-22 44-78 44s-78-16-78-44c0-20 14-36 28-50Z"
                  stroke="currentColor"
                  strokeWidth="2"
                />
              </svg>
            </div>
            <p className="inline-flex items-center gap-2 text-sm uppercase tracking-[0.3em] text-blush-600">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white/70 text-blush-500">
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path
                    d="M5 12.5c2-2 3-5.1 3.2-6.8L10 8.4l1.8-2.7c.2 1.7 1.2 4.8 3.2 6.8 1.8 1.7 3.3 3.5 3.3 5.6 0 2.7-2.2 4.3-6.5 4.3s-6.5-1.6-6.5-4.3c0-2.1 1.5-3.9 3.4-5.6Z"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              SlimFox
            </p>
            <h1 className="text-4xl font-semibold leading-tight text-ink-900 sm:text-5xl">
              SlimFox — центр коррекции фигуры, где ты становишься собой.
            </h1>
            <p className="text-base text-ink-700">
              Индивидуальные программы, эстетика тела и забота о каждой детали. Вместе мы создадим силуэт, который ты
              полюбишь.
            </p>
            <div className="flex flex-wrap gap-4">
              <Button href="#booking">Начать трансформацию</Button>
              <Button href="/services" variant="secondary">
                Наши услуги
              </Button>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-ink-700">
              <span>🦊 Тонкий силуэт без давления</span>
              <span>✨ Эстетика и наука</span>
              <span>🫶 Забота о каждой детали</span>
            </div>
          </div>
          {weeklyRituals.length > 0 ? (
            <div className="relative">
              <div className="absolute -left-6 -top-6 h-full w-full rounded-3xl bg-gradient-to-br from-blush-100 via-peach-50 to-white" />
              <div className="relative rounded-3xl bg-white/85 p-8 shadow-card ring-1 ring-blush-100/70 backdrop-blur">
                <WeeklyRitualCarousel rituals={weeklyRituals} />
              </div>
            </div>
          ) : null}
        </Container>
      </Section>

      <Section>
        <Container>
          <div className="flex items-end justify-between gap-6">
            <div>
              <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Каталог SlimFox</p>
              <h2 className="mt-3 text-3xl font-semibold text-ink-900">Мы предлагаем не процедуры, а искусство преображения.</h2>
              <p className="mt-3 text-sm text-ink-600">
                Полный каталог доступен на странице «Смотреть все», если вы не нашли нужную услугу в блоке ниже.
              </p>
            </div>
            <Button href="/services" variant="ghost" className="hidden sm:inline-flex">
              Смотреть все →
            </Button>
          </div>
          <div className="mt-8 grid min-h-[200px] gap-6 md:grid-cols-2 lg:grid-cols-3">
            {servicesPreview.map((service) => (
              <ServiceCard key={service.slug} service={service} />
            ))}
          </div>
        </Container>
      </Section>

      <Section className="bg-gradient-to-br from-blush-50 via-white to-peach-50">
        <Container className="grid gap-10 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Почему SlimFox</p>
            <h2 className="text-3xl font-semibold text-ink-900">
              Почему выбирают нас? Потому что мы видим в вас не клиента, а личность.
            </h2>
            <p className="text-base text-ink-700">
              В каждой программе мы объединяем грацию, силу и мягкость — как в образе лисы. Это синтез аппаратных
              методик, ручных техник и эстетического сопровождения, где результат достигается бережно и осознанно.
            </p>
            <p className="text-base text-ink-700">
              SlimFox — это пространство, где коррекция фигуры становится персональной историей, а не набором процедур.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            {slimfoxHighlights.map((item) => (
              <Card key={item.title}>
                <div className="text-blush-500">{item.icon}</div>
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
              Мы создали SlimFox как место, где научный подход к телу сочетается с мягкой эстетикой и приватной атмосферой.
              Наши специалисты бережно подбирают техники, учитывая ваш ритм, образ жизни и желания.
            </p>
            <p className="text-base text-ink-700">
              В интерьере — пастельные оттенки, мягкий текстиль и тишина. В завершение мы предлагаем тёплый ритуал,
              чтобы закрепить ощущение лёгкости и уверенности.
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

      {publicReviews.length > 0 ? (
        <Section id="reviews" className="bg-white/70">
          <Container>
            <div className="flex flex-col gap-3">
              <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Отзывы</p>
              <h2 className="text-3xl font-semibold text-ink-900">Гости рассказывают о своих ощущениях</h2>
            </div>
            <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
              {publicReviews.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
            </div>
          </Container>
        </Section>
      ) : null}

      <Section className="bg-gradient-to-br from-blush-50 via-white to-peach-50">
        <Container className="grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-4">
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Обращение</p>
            <h2 className="text-3xl font-semibold text-ink-900">
              Ты — не просто тело. Ты — стиль, характер, грация.
            </h2>
            <p className="text-base text-ink-700">
              Мы создаём бережные программы коррекции фигуры, которые подчёркивают твою индивидуальность и помогают
              почувствовать себя уверенно. SlimFox — про уважение к телу, его ритму и твоей внутренней силе.
            </p>
          </div>
          <div className="flex flex-col gap-4 rounded-3xl bg-white/80 p-8 shadow-card ring-1 ring-blush-100/70">
            <p className="text-sm text-ink-700">
              Начни путь к себе с мягкой консультации — мы обсудим цели, подберём формат и выстроим маршрут трансформации.
            </p>
            <Button href="#booking" className="w-fit">
              Записаться на консультацию
            </Button>
          </div>
        </Container>
      </Section>

      <Section id="booking">
        <Container className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Запись</p>
            <h2 className="mt-3 text-3xl font-semibold text-ink-900">Готовы начать путь к себе?</h2>
            <p className="mt-4 text-base text-ink-700">
              SlimFox — это место, где встречаются наука, эстетика и забота. Оставьте заявку, и мы поможем выбрать
              комфортное время и программу.
            </p>
            <div className="mt-6 space-y-3 text-sm text-ink-700">
              <p className="flex items-center gap-2">📞 {contacts.phone}</p>
              <p className="flex items-center gap-2">📍 {contacts.address}</p>
              <p className="flex items-center gap-2">📸 Instagram: @slimfox</p>
              <p className="flex items-center gap-2">✉️ hello@slimfox.ru</p>
              <p className="flex items-center gap-2">🕒 Ежедневно 10:00–21:00</p>
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
              {selectedServiceId && selectedDate && slotsLoaded && slots.length === 0 ? (
                <p className="mt-2 text-xs text-rose-600">
                  Нет доступного времени на выбранную дату. Выберите другую дату.
                </p>
              ) : null}
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
