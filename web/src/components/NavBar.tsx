import Link from "next/link";
import Image from "next/image";
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
    <header className="fixed top-0 z-50 w-full overflow-hidden bg-[url('/images/banner.svg')] bg-cover bg-center bg-no-repeat backdrop-blur-md before:absolute before:inset-0 before:z-0 before:bg-white/65 before:content-['']">
      <Container className="relative z-10 flex h-24 items-center justify-between">
        <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-ink-900">
          <Image src="/images/logo-icon.svg" alt="SlimFox logo" width={24} height={24} className="h-6 w-6" priority />
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
