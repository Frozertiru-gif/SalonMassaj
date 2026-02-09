import { adminFetch } from "@/lib/api";
import type { WeeklyRitual } from "@/lib/types";
import { Button } from "@/components/Button";
import { Container } from "@/components/Container";
import { WeeklyRitualList } from "./WeeklyRitualList";

export default async function AdminWeeklyRitualsPage() {
  const rituals = await adminFetch<WeeklyRitual[]>("/admin/weekly-rituals");

  return (
    <Container className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Ритуал недели</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">Ритуалы недели</h2>
        </div>
        <Button href="/admin/weekly-rituals/new" variant="secondary">
          Добавить
        </Button>
      </div>
      <WeeklyRitualList rituals={rituals} />
    </Container>
  );
}
