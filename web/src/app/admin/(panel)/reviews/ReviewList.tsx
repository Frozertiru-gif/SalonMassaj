"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { Review } from "@/lib/types";
import { deleteReview } from "../../actions";

type ReviewListProps = {
  reviews: Review[];
};

const initialState = { error: undefined, success: undefined };

export function ReviewList({ reviews }: ReviewListProps) {
  if (reviews.length === 0) {
    return <Card>Отзывы пока не добавлены.</Card>;
  }

  return (
    <div className="space-y-3">
      {reviews.map((review) => (
        <ReviewRow key={review.id} review={review} />
      ))}
    </div>
  );
}

function ReviewRow({ review }: { review: Review }) {
  const [deleteState, deleteAction] = useFormState(deleteReview, initialState);

  return (
    <Card className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-ink-900">{review.author_name}</p>
        <p className="text-xs text-ink-500">{review.source || "Без источника"}</p>
      </div>
      <div className="text-xs uppercase tracking-[0.2em] text-blush-600">
        {review.is_published ? "Опубликован" : "Скрыт"}
      </div>
      <div className="flex items-center gap-3">
        <Button href={`/admin/reviews/${review.id}`} variant="ghost">
          Редактировать
        </Button>
        <form action={deleteAction}>
          <input type="hidden" name="id" value={review.id} />
          <Button type="submit" variant="secondary">
            Удалить
          </Button>
        </form>
      </div>
      {deleteState.error ? <p className="text-sm text-red-600 w-full">{deleteState.error}</p> : null}
      {deleteState.success ? <p className="text-sm text-green-600 w-full">{deleteState.success}</p> : null}
    </Card>
  );
}
