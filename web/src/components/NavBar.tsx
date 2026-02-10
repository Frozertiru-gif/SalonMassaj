import Link from "next/link";
import { Container } from "@/components/Container";

const navItems = [
  { label: "Услуги", href: "/services" },
  { label: "Мастера", href: "/masters" },
  { label: "О нас", href: "/#about" },
  { label: "Отзывы", href: "/#reviews" },
  { label: "Запись", href: "/#booking" }
];

export function NavBar() {
  return (
    <header className="fixed top-0 z-50 w-full border-b border-blush-100 bg-white/80 backdrop-blur-md">
      <Container className="flex h-20 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-ink-900">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blush-100 text-blush-600">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path
                d="M4 12.5c2.3-2.2 3.4-5.6 3.7-7.5l2.6 3.2 2.5-3.2c.3 1.9 1.4 5.3 3.7 7.5 2.1 2 3.7 4 3.7 6.8 0 3.2-2.7 5.2-8 5.2s-8-2-8-5.2c0-2.8 1.6-4.8 3.8-6.8Z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          SlimFox
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
          Начать трансформацию
        </Link>
      </Container>
    </header>
  );
}
