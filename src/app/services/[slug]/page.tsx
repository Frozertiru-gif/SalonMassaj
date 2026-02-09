import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Button } from "@/components/Button";
import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";
import { services } from "@/data/services";

interface ServicePageProps {
  params: { slug: string };
}

export function generateMetadata({ params }: ServicePageProps): Metadata {
  const service = services.find((item) => item.slug === params.slug);

  if (!service) {
    return {
      title: "Услуга не найдена — Salon Massaj"
    };
  }

  return {
    title: `${service.title} — Salon Massaj`,
    description: service.shortDescription
  };
}

export default function ServicePage({ params }: ServicePageProps) {
  const service = services.find((item) => item.slug === params.slug);

  if (!service) {
    notFound();
  }

  return (
    <Section className="pt-12">
      <Container className="space-y-10">
        <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Badge>{service.category}</Badge>
            <div className="space-y-3">
              <h1 className="text-4xl font-semibold text-ink-900">{service.title}</h1>
              <p className="text-base text-ink-700">{service.description}</p>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-ink-700">
              <span>⏳ {service.durationMin} минут</span>
              <span>💗 от {service.priceFrom.toLocaleString("ru-RU")} ₽</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {service.tags.map((tag) => (
                <span key={tag} className="rounded-full bg-blush-50 px-3 py-1 text-xs text-blush-600">
                  {tag}
                </span>
              ))}
            </div>
            <Button href={`/?service=${encodeURIComponent(service.title)}#booking`}>Записаться</Button>
          </div>
          <Card className="h-80">
            <div className="flex h-full items-center justify-center rounded-2xl bg-gradient-to-br from-blush-100 via-white to-blush-50 text-sm text-blush-500">
              Изображение услуги (плейсхолдер)
            </div>
          </Card>
        </div>
        <Card className="grid gap-6 sm:grid-cols-3">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-blush-500">Что входит</p>
            <p className="mt-3 text-sm text-ink-700">Мягкое начало, прогрев, основной ритм и финальный релакс.</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-blush-500">Для кого</p>
            <p className="mt-3 text-sm text-ink-700">Тем, кто хочет восстановить баланс и почувствовать лёгкость.</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-blush-500">Советы</p>
            <p className="mt-3 text-sm text-ink-700">Пейте воду после сеанса и выделите время для отдыха.</p>
          </div>
        </Card>
      </Container>
    </Section>
  );
}
