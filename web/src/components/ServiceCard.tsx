import Link from "next/link";
import { Badge } from "@/components/Badge";
import { Card } from "@/components/Card";
import { formatPrice, getDiscountedPrice } from "@/lib/pricing";
import type { Service } from "@/lib/types";

interface ServiceCardProps {
  service: Service;
}

export function ServiceCard({ service }: ServiceCardProps) {
  const discountedFrom = getDiscountedPrice(service.price_from, service.discount_percent);
  const hasDiscount = service.discount_percent && service.discount_percent > 0;
  return (
    <Card className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <Badge>{service.category?.title ?? "Услуга"}</Badge>
        <div className="text-right text-xs text-ink-700">
          {hasDiscount ? (
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-blush-100 px-2 py-0.5 text-[10px] font-semibold text-blush-700">
                -{service.discount_percent}%
              </span>
              <span className="text-xs font-semibold text-ink-900">от {formatPrice(discountedFrom)} ₽</span>
            </div>
          ) : (
            <span>от {formatPrice(service.price_from)} ₽</span>
          )}
          {hasDiscount ? (
            <div className="text-[10px] text-ink-400 line-through">от {formatPrice(service.price_from)} ₽</div>
          ) : null}
        </div>
      </div>
      <div className="space-y-2">
        <h3 className="text-lg font-semibold text-ink-900">{service.title}</h3>
        <p className="text-sm text-ink-700">{service.short_description}</p>
      </div>
      <div className="flex flex-wrap gap-2">
        {service.tags.map((tag) => (
          <span key={tag} className="rounded-full bg-blush-50 px-3 py-1 text-xs text-blush-600">
            {tag}
          </span>
        ))}
      </div>
      <div className="mt-auto flex items-center justify-between text-sm text-ink-700">
        <span>{service.duration_min} мин</span>
        <Link
          href={`/services/${encodeURIComponent(service.slug)}`}
          className="font-medium text-blush-600 hover:text-blush-700"
        >
          Подробнее
        </Link>
      </div>
    </Card>
  );
}
