import { notFound } from "next/navigation";
import { adminFetch } from "@/lib/api";
import type { WeeklyRitual } from "@/lib/types";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { updateWeeklyRitual } from "../../../actions";
import { WeeklyRitualDeleteForm } from "../WeeklyRitualDeleteForm";
import { WeeklyRitualForm } from "../WeeklyRitualForm";

type WeeklyRitualEditPageProps = {
  params: { id: string };
};

export default async function WeeklyRitualEditPage({ params }: WeeklyRitualEditPageProps) {
  const ritualId = Number(params.id);
  if (Number.isNaN(ritualId)) {
    notFound();
  }

  const rituals = await adminFetch<WeeklyRitual[]>("/admin/weekly-rituals");
  const ritual = rituals.find((item) => item.id === ritualId);
  if (!ritual) {
    notFound();
  }

  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Ритуал недели</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Редактирование ритуала</h2>
      </div>
      <WeeklyRitualForm action={updateWeeklyRitual} initialData={ritual} submitLabel="Сохранить" />
      <Card className="space-y-3">
        <h3 className="text-lg font-semibold text-ink-900">Удалить ритуал</h3>
        <WeeklyRitualDeleteForm ritualId={ritual.id} />
      </Card>
    </Container>
  );
}
