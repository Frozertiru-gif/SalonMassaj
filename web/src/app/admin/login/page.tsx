import { loginAdmin } from "../actions";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";

export default function AdminLoginPage() {
  return (
    <Section className="pt-12">
      <Container className="flex justify-center">
        <Card className="w-full max-w-md">
          <h1 className="text-2xl font-semibold text-ink-900">Вход в админку</h1>
          <p className="mt-2 text-sm text-ink-600">Используйте учётные данные администратора.</p>
          <form action={loginAdmin} className="mt-6 space-y-4">
            <div>
              <label className="text-xs font-medium text-ink-700">Email</label>
              <input
                name="email"
                type="email"
                required
                className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900"
                placeholder="owner@example.com"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-ink-700">Пароль</label>
              <input
                name="password"
                type="password"
                required
                className="mt-2 w-full rounded-2xl border border-blush-100 bg-white px-4 py-3 text-sm text-ink-900"
                placeholder="••••••"
              />
            </div>
            <Button type="submit" className="w-full">
              Войти
            </Button>
          </form>
        </Card>
      </Container>
    </Section>
  );
}
