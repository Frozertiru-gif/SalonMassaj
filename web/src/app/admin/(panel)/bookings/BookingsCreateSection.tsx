"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/Button";
import { CollapsibleSection } from "@/components/admin/CollapsibleSection";
import type { Service } from "@/lib/types";
import { AdminBookingCreateForm } from "./AdminBookingCreateForm";

export function BookingsCreateSection({ services }: { services: Service[] }) {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const createSectionRef = useRef<HTMLDivElement | null>(null);

  const handleOpenCreate = () => {
    setIsCreateOpen(true);
    createSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Записи</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">Управление заявками</h2>
        </div>
        <Button type="button" variant="secondary" onClick={handleOpenCreate}>
          Добавить
        </Button>
      </div>

      <div ref={createSectionRef}>
        <CollapsibleSection title="Создать запись" open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <div className="pt-2">
            <AdminBookingCreateForm services={services} onSuccess={() => setIsCreateOpen(false)} />
          </div>
        </CollapsibleSection>
      </div>
    </>
  );
}
