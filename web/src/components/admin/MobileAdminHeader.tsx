"use client";

type MobileAdminHeaderProps = {
  title: string;
  onMenuOpen: () => void;
};

export function MobileAdminHeader({ title, onMenuOpen }: MobileAdminHeaderProps) {
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-blush-100 bg-white/95 backdrop-blur md:hidden">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between gap-3 px-4">
        <button
          type="button"
          onClick={onMenuOpen}
          className="rounded-lg border border-blush-100 px-3 py-1.5 text-sm text-ink-700"
          aria-label="Открыть меню"
        >
          ☰
        </button>
        <p className="truncate text-sm font-semibold text-ink-900">{title}</p>
        <div className="w-10" aria-hidden />
      </div>
    </header>
  );
}
