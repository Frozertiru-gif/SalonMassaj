import { Container } from "@/components/Container";

export function Footer() {
  return (
    <footer className="border-t border-blush-100 bg-white/70 py-12">
      <Container className="grid gap-8 text-sm text-ink-700 md:grid-cols-3">
        <div>
          <p className="text-base font-semibold text-ink-900">SlimFox</p>
          <p className="mt-3">
            SlimFox — центр коррекции фигуры, где каждая лисичка находит свой идеальный силуэт.
          </p>
        </div>
        <div>
          <p className="text-base font-semibold text-ink-900">Контакты</p>
          <ul className="mt-3 space-y-2">
            <li>Телефон: +7 (999) 123-45-67</li>
            <li>Адрес: Москва, ул. Пудровая, 12</li>
            <li>Email: hello@slimfox.ru</li>
          </ul>
        </div>
        <div>
          <p className="text-base font-semibold text-ink-900">Мы в соцсетях</p>
          <ul className="mt-3 space-y-2">
            <li>Instagram: @slimfox</li>
            <li>Telegram: @slimfox</li>
            <li>Часы работы: ежедневно 10:00–21:00</li>
          </ul>
        </div>
      </Container>
    </footer>
  );
}
