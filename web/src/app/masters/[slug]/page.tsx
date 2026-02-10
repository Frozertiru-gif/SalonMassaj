import Link from "next/link";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { publicFetch } from "@/lib/api";
import type { Master } from "@/lib/types";

export default async function MasterDetailsPage({ params }: { params: { slug: string } }) {
  const master = await publicFetch<Master>(`/public/masters/${params.slug}`, { revalidate: 300 });

  return (
    <Container className="space-y-8 py-16">
      <div className="grid gap-8 lg:grid-cols-[300px_1fr]">
        <div className="h-72 rounded-3xl bg-blush-100/70 overflow-hidden flex items-center justify-center text-ink-500">
          {master.photo_url ? <img src={master.photo_url} alt={master.name} className="h-full w-full object-cover" /> : "Фото мастера"}
        </div>
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Профиль мастера</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink-900">{master.name}</h1>
          <p className="mt-4 text-ink-700">{master.bio ?? master.short_bio ?? "Описание появится скоро."}</p>
        </div>
      </div>
      <Card>
        <h2 className="text-xl font-semibold text-ink-900">Услуги мастера</h2>
        <ul className="mt-4 space-y-2 text-sm text-ink-700">
          {master.services?.map((service) => (
            <li key={service.id}>
              <Link className="text-blush-700" href={`/services/${service.slug}`}>{service.title}</Link>
            </li>
          ))}
        </ul>
      </Card>
    </Container>
  );
}
