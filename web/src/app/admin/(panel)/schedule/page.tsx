import { adminFetch } from "@/lib/api";
import { Container } from "@/components/Container";
import type { AdminAvailabilityResponse, AdminScheduleResponse } from "@/lib/types";
import { ScheduleClient } from "./schedule-client";

function isoDate(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export default async function AdminSchedulePage() {
  const today = isoDate(new Date());
  const [schedule, availability] = await Promise.all([
    adminFetch<AdminScheduleResponse>(`/admin/schedule?date=${today}&mode=day`),
    adminFetch<AdminAvailabilityResponse>(`/admin/availability?date=${today}&service_id=1`)
  ]);

  return (
    <Container>
      <ScheduleClient initialDate={today} initialSchedule={schedule} initialAvailability={availability} />
    </Container>
  );
}
