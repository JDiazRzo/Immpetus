import type { Metadata } from "next";
import { Bricolage_Grotesque, Public_Sans } from "next/font/google";
import { SITE } from "@/lib/site";
import "./globals.css";

const bricolage = Bricolage_Grotesque({
  variable: "--font-bricolage",
  subsets: ["latin"],
  weight: ["600", "700", "800"],
});

const publicSans = Public_Sans({
  variable: "--font-public-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE.url),
  title: {
    default: "Immpetus Soluciones · Talento humano y gestión organizacional",
    template: "%s · Immpetus Soluciones",
  },
  description:
    "Consultoría en talento humano en Colombia. Selección de personal, BPO, formación y diseño de procesos. Vea nuestras vacantes activas.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es-CO" className={`${bricolage.variable} ${publicSans.variable}`}>
      <body className="flex min-h-dvh flex-col">{children}</body>
    </html>
  );
}
