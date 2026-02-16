import { adminFetch } from "@/lib/api";
import { Container } from "@/components/Container";
import type { AdminAvailabilityResponse, AdminScheduleResponse } from "@/lib/types";
import { ScheduleClient } from "./schedule-client";
import { AdminErrorBox } from "./AdminErrorBox";

function isoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export default async function AdminSchedulePage() {
  const today = isoDate(new Date());

  try {
    const [schedule, availability] = await Promise.all([
      adminFetch<AdminScheduleResponse>(`/admin/schedule?date=${today}&mode=day`),
      adminFetch<AdminAvailabilityResponse>(`/admin/availability?date=${today}&service_id=1`)
    ]);

    return (
      <Container>
        <ScheduleClient initialDate={today} initialSchedule={schedule} initialAvailability={availability} />
      </Container>
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Неизвестная ошибка";
    return (
      <Container>
        <AdminErrorBox message={message} />
      </Container>
    );
  }
}
