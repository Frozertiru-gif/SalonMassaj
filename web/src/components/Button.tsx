import type { ReactNode } from "react";
import Link from "next/link";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = {
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  variant?: ButtonVariant;
  className?: string;
  type?: "button" | "submit" | "reset";
};

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-blush-400 via-blush-500 to-peach-300 text-white shadow-soft hover:from-blush-500 hover:via-blush-600 hover:to-peach-400",
  secondary: "bg-white text-blush-700 border border-blush-200 hover:border-blush-300",
  ghost: "text-ink-700 hover:text-blush-700"
};

export function Button({
  children,
  href,
  onClick,
  variant = "primary",
  className,
  type = "button"
}: ButtonProps) {
  const classes = `inline-flex items-center justify-center rounded-full px-6 py-3 text-sm font-medium transition ${variantClasses[variant]} ${
    className ?? ""
  }`.trim();

  if (href) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} onClick={onClick} className={classes}>
      {children}
    </button>
  );
}
