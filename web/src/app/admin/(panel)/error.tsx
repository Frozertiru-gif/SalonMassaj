"use client";

import { Button } from "@/components/Button";
import { Container } from "@/components/Container";

export default function AdminPanelError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Container className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-blush-600">Админка</p>
        <h2 className="mt-2 text-2xl font-semibold text-ink-900">Сервис временно недоступен</h2>
      </div>
      <p className="text-ink-600">Не удалось загрузить данные. Попробуйте обновить страницу чуть позже.</p>
      <Button type="button" onClick={reset} variant="secondary">
        Повторить
      </Button>
    </Container>
  );
}
