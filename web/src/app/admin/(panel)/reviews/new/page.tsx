import { Container } from "@/components/Container";
import { createReview } from "../../../actions";
import { ReviewForm } from "../ReviewForm";

export default function ReviewNewPage() {
  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Отзывы</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Новый отзыв</h2>
      </div>
      <ReviewForm action={createReview} submitLabel="Создать" />
    </Container>
  );
}
