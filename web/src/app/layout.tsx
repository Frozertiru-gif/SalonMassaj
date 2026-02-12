import "./globals.css";
import type { Metadata } from "next";
import { Footer } from "@/components/Footer";
import { NavBar } from "@/components/NavBar";

export const metadata: Metadata = {
  title: "SlimFox — центр коррекции фигуры и эстетики тела",
  description:
    "SlimFox объединяет индивидуальные программы, эстетику тела и заботу о каждой детали для создания силуэта, который вы полюбите.",
  formatDetection: {
    telephone: false
  },
  icons: {
    icon: "/images/logo-icon.svg",
    shortcut: "/images/logo-icon.svg",
    apple: "/images/logo-icon.svg"
  }
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>
        <NavBar />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
