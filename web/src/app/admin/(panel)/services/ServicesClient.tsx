"use client";

import { useRef, useState } from "react";
import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { CollapsibleSection } from "@/components/admin/CollapsibleSection";
import type { Service, ServiceCategory } from "@/lib/types";
import { deleteService } from "../../actions";
import { ServiceCreateForm } from "./new/ServiceCreateForm";

type ServicesClientProps = {
  services: Service[];
  categories: ServiceCategory[];
};

const initialState = { error: undefined, success: undefined };

export function ServicesClient({ services, categories }: ServicesClientProps) {
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
          <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Услуги</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink-900">Каталог услуг</h2>
        </div>
        <Button type="button" variant="secondary" onClick={handleOpenCreate}>
          Добавить
        </Button>
      </div>

      <div ref={createSectionRef}>
        <CollapsibleSection title="Добавить услугу" open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <div className="pt-2">
            <ServiceCreateForm categories={categories} onSuccess={() => setIsCreateOpen(false)} />
          </div>
        </CollapsibleSection>
      </div>

      <div className="space-y-3">
        {services.map((service) => (
          <ServiceRow key={service.id} service={service} />
        ))}
      </div>
    </>
  );
}

function ServiceRow({ service }: { service: Service }) {
  const [deleteState, deleteAction] = useFormState(deleteService, initialState);

  return (
    <Card className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-ink-900">{service.title}</p>
      </div>
      <div className="text-sm text-ink-600">{service.duration_min} мин</div>
      <div className="text-sm text-ink-600">от {service.price_from} ₽</div>
      <div className="flex items-center gap-3">
        <Button href={`/admin/services/${service.id}`} variant="ghost">
          Редактировать
        </Button>
        <form action={deleteAction}>
          <input type="hidden" name="id" value={service.id} />
          <Button type="submit" variant="secondary">
            Удалить
          </Button>
        </form>
      </div>
      {deleteState.error ? <p className="w-full text-sm text-red-600">{deleteState.error}</p> : null}
      {deleteState.success ? <p className="w-full text-sm text-green-600">{deleteState.success}</p> : null}
    </Card>
  );
}
