"use client";

import { useFormState } from "react-dom";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import type { Service } from "@/lib/types";
import { deleteService } from "../../actions";

type ServicesClientProps = {
  services: Service[];
};

const initialState = { error: undefined, success: undefined };

export function ServicesClient({ services }: ServicesClientProps) {
  return (
    <div className="space-y-3">
      {services.map((service) => (
        <ServiceRow key={service.id} service={service} />
      ))}
    </div>
  );
}

function ServiceRow({ service }: { service: Service }) {
  const [deleteState, deleteAction] = useFormState(deleteService, initialState);

  return (
    <Card className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p className="text-sm font-medium text-ink-900">{service.title}</p>
        <p className="text-xs text-ink-500">{service.slug}</p>
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
