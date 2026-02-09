import Link from "next/link";
import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import type { Service } from "@/data/services";

interface ServiceCardProps {
  service: Service;
}

export function ServiceCard({ service }: ServiceCardProps) {
  return (
    <Card className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <Badge>{service.category}</Badge>
        <span className="text-xs text-ink-700">от {service.priceFrom.toLocaleString("ru-RU")} ₽</span>
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-ink-900">{service.title}</h3>
        <p className="text-sm text-ink-700">{service.shortDescription}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {service.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-blush-50 px-3 py-1 text-xs text-blush-600">
            {tag}
          </span>
        ))}
      </div>
      <div className="mt-auto flex items-center justify-between text-sm text-ink-700">
        <span>{service.durationMin} мин</span>
        <Link href={`/services/${service.slug}`} className="font-medium text-blush-600 hover:text-blush-700">
          Подробнее
        </Link>
      </div>
    </Card>
  );
}
