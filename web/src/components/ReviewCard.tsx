import { Card } from "@/components/Card";
import type { Review } from "@/lib/types";

interface ReviewCardProps {
  review: Review;
}

export function ReviewCard({ review }: ReviewCardProps) {
  const stars =
    review.rating && review.rating > 0 ? "★".repeat(review.rating) + "☆".repeat(5 - review.rating) : null;
  return (
    <Card className="flex h-full flex-col gap-4">
      <p className="text-sm text-ink-700">“{review.text}”</p>
      <div>
        <p className="text-sm font-semibold text-ink-900">{review.author_name}</p>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-600">
          {stars ? <span className="text-blush-500">{stars}</span> : null}
          {review.source ? <span>{review.source}</span> : null}
        </div>
      </div>
    </Card>
  );
}
