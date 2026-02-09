import { notFound } from "next/navigation";
import { adminFetch } from "@/lib/api";
import type { Review } from "@/lib/types";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { updateReview } from "../../../actions";
import { ReviewDeleteForm } from "../ReviewDeleteForm";
import { ReviewForm } from "../ReviewForm";

type ReviewEditPageProps = {
  params: { id: string };
};

export default async function ReviewEditPage({ params }: ReviewEditPageProps) {
  const reviewId = Number(params.id);
  if (Number.isNaN(reviewId)) {
    notFound();
  }

  const reviews = await adminFetch<Review[]>("/admin/reviews");
  const review = reviews.find((item) => item.id === reviewId);
  if (!review) {
    notFound();
  }

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Отзывы</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Редактирование отзыва</h2>
      </div>
      <ReviewForm action={updateReview} initialData={review} submitLabel="Сохранить" />
      <Card className="space-y-3">
        <h3 className="text-lg font-semibold text-ink-900">Удалить отзыв</h3>
        <ReviewDeleteForm reviewId={review.id} />
      </Card>
    </Container>
  );
}
