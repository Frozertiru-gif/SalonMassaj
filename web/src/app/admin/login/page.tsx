import { LoginForm } from "./LoginForm";
import { Card } from "@/components/Card";
import { Container } from "@/components/Container";
import { Section } from "@/components/Section";
import { normalizeAdminNextPath } from "@/lib/auth";

export default function AdminLoginPage({ searchParams }: { searchParams?: { next?: string } }) {
  const nextPath = normalizeAdminNextPath(searchParams?.next);

  return (
    <Section className="pt-12">
      <Container className="flex justify-center">
        <Card className="w-full max-w-md">
          <h1 className="text-2xl font-semibold text-ink-900">Вход в админку</h1>
          <p className="mt-2 text-sm text-ink-600">Используйте учётные данные администратора.</p>
          <LoginForm nextPath={nextPath} />
        </Card>
      </Container>
    </Section>
  );
}
