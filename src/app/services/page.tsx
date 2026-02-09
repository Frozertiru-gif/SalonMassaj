import type { Metadata } from "next";
import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";
import { ServiceCard } from "@/components/ServiceCard";
import { services } from "@/data/services";

export const metadata: Metadata = {
  title: "Услуги — Salon Massaj",
  description: "Каталог массажных программ и спа-ритуалов Salon Massaj."
};

export default function ServicesPage() {
  return (
    <Section className="pt-12">
      <Container>
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Каталог</p>
            <h1 className="mt-3 text-4xl font-semibold text-ink-900">Все услуги</h1>
            <p className="mt-4 max-w-2xl text-base text-ink-700">
              От расслабляющих ритуалов до восстановительных программ — выберите формат, который подойдёт вашему
              состоянию сегодня.
            </p>
          </div>
          <Button href="/#booking" variant="secondary">
            Записаться
          </Button>
        </div>
        <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => (
            <ServiceCard key={service.slug} service={service} />
          ))}
        </div>
      </Container>
    </Section>
  );
}
