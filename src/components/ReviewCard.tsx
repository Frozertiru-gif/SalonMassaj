import { Card } from "@/components/Card";
import type { Review } from "@/data/reviews";

interface ReviewCardProps {
  review: Review;
}

export function ReviewCard({ review }: ReviewCardProps) {
  return (
    <Card className="flex h-full flex-col gap-4">
      <p className="text-sm text-ink-700">“{review.text}”</p>
      <div>
        <p className="text-sm font-semibold text-ink-900">{review.name}</p>
        <p className="text-xs text-ink-600">{review.service}</p>
      </div>
    </Card>
  );
}
