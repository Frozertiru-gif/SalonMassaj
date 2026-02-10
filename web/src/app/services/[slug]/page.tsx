import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Button } from "@/components/Button";
import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";
import { publicFetch } from "@/lib/api";
import { formatPrice, getDiscountedPrice } from "@/lib/pricing";
import type { Service } from "@/lib/types";

interface ServicePageProps {
  params: { slug: string };
}

export async function generateMetadata({ params }: ServicePageProps): Promise<Metadata> {
  try {
    const encodedSlug = encodeURIComponent(params.slug);
    const service = await publicFetch<Service>(`/public/services/${encodedSlug}`);
    return {
      title: `${service.title} — Salon Massaj`,
      description: service.short_description
    };
  } catch {
    return {
      title: "Услуга не найдена — Salon Massaj"
    };
  }
}

export default async function ServicePage({ params }: ServicePageProps) {
  if (process.env.NODE_ENV !== "production") {
    console.log(`[services/[slug]] Matched slug: ${params.slug}`);
  }

  let service: Service | null = null;
  try {
    const encodedSlug = encodeURIComponent(params.slug);
    service = await publicFetch<Service>(`/public/services/${encodedSlug}`);
  } catch {
    service = null;
  }

  if (!service) {
    notFound();
  }

  const discountedFrom = getDiscountedPrice(service.price_from, service.discount_percent);
  const hasDiscount = service.discount_percent && service.discount_percent > 0;

  return (
    <Section className="pt-12">
      <Container className="space-y-10">
        <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <Badge>{service.category?.title ?? "Услуга"}</Badge>
            <div className="space-y-3">
              <h1 className="text-4xl font-semibold text-ink-900">{service.title}</h1>
              <p className="text-base text-ink-700">{service.description}</p>
            </div>
            <div className="flex flex-wrap gap-4 text-sm text-ink-700">
              <span>⏳ {service.duration_min} минут</span>
              <span className="flex items-center gap-2">
                💗 от {formatPrice(discountedFrom)} ₽
                {hasDiscount ? (
                  <span className="text-xs text-ink-400 line-through">от {formatPrice(service.price_from)} ₽</span>
                ) : null}
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {service.tags.map((tag) => (
                <span key={tag} className="rounded-full bg-blush-50 px-3 py-1 text-xs text-blush-600">
                  {tag}
                </span>
              ))}
            </div>
            <Button href={`/?service=${encodeURIComponent(service.slug)}#booking`}>Записаться</Button>
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
