import Link from "next/link";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { publicFetch } from "@/lib/api";
import type { Master } from "@/lib/types";

export default async function MastersPage() {
  const masters = await publicFetch<Master[]>("/public/masters", { revalidate: 300 });

  return (
    <Container className="space-y-6 py-16">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Команда</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink-900">Наши мастера</h1>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {masters.map((master) => (
          <Card key={master.id}>
            <div className="h-44 rounded-2xl bg-blush-100/70 text-sm text-ink-500 flex items-center justify-center">
              {master.photo_url ? <img src={master.photo_url} alt={master.name} className="h-full w-full rounded-2xl object-cover" /> : "Фото мастера"}
            </div>
            <h2 className="mt-4 text-xl font-semibold text-ink-900">{master.name}</h2>
            <p className="mt-2 text-sm text-ink-700">{master.short_bio ?? "Эксперт SlimFox"}</p>
            <Link href={`/masters/${master.slug}`} className="mt-4 inline-block text-sm font-medium text-blush-700">Подробнее →</Link>
          </Card>
        ))}
      </div>
    </Container>
  );
}
