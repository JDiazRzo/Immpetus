import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

type Props = {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary" | "inverse";
  className?: string;
};

export function ButtonLink({ href, children, variant = "primary", className }: Props) {
  return (
    <Link
      href={href}
      className={cn(
        "inline-flex min-h-11 items-center justify-center rounded-chip px-5 py-3 text-base font-bold transition-colors",
        variant === "primary" && "bg-action text-white hover:bg-[#2c1490]",
        variant === "secondary" && "border-[1.5px] border-ink bg-surface text-ink hover:bg-paper",
        variant === "inverse" && "border-[1.5px] border-white/70 text-white hover:bg-white hover:text-ink",
        className,
      )}
    >
      {children}
    </Link>
  );
}
