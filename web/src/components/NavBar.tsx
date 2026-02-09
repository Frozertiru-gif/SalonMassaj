import Link from "next/link";
import { Container } from "@/components/Container";

const navItems = [
  { label: "Услуги", href: "/services" },
  { label: "О нас", href: "/#about" },
  { label: "Отзывы", href: "/#reviews" },
  { label: "Запись", href: "/#booking" }
];

export function NavBar() {
  return (
    <header className="fixed top-0 z-50 w-full border-b border-blush-100 bg-white/80 backdrop-blur-md">
      <Container className="flex h-20 items-center justify-between">
        <Link href="/" className="text-lg font-semibold text-ink-900">
          Salon Massaj
        </Link>
        <nav className="hidden items-center gap-6 text-sm font-medium text-ink-700 md:flex">
          {navItems.map((item) => (
            <Link key={item.label} href={item.href} className="transition hover:text-blush-600">
              {item.label}
            </Link>
          ))}
        </nav>
        <Link
          href="/#booking"
          className="rounded-full border border-blush-200 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-blush-700 transition hover:border-blush-300"
        >
          Записаться
        </Link>
      </Container>
    </header>
  );
}
