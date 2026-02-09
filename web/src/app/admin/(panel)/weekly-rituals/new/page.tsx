import { Container } from "@/components/Container";
import { createWeeklyRitual } from "../../../actions";
import { WeeklyRitualForm } from "../WeeklyRitualForm";

export default function WeeklyRitualNewPage() {
  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Ритуал недели</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Новый ритуал</h2>
      </div>
      <WeeklyRitualForm action={createWeeklyRitual} submitLabel="Создать" />
    </Container>
  );
}
