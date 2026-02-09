import { adminFetch } from "@/lib/api";
import type { Review } from "@/lib/types";
import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { ReviewList } from "./ReviewList";

export default async function AdminReviewsPage() {
  const reviews = await adminFetch<Review[]>("/admin/reviews");

  return (
    <Container className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Отзывы</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">Отзывы клиентов</h2>
        </div>
        <Button href="/admin/reviews/new" variant="secondary">
          Добавить
        </Button>
      </div>
      <ReviewList reviews={reviews} />
    </Container>
  );
}
