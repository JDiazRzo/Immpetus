import { ButtonLink } from "@/components/ButtonLink";
import { Container } from "@/components/Container";

export default function NotFound() {
  return (
    <Container className="flex flex-col items-start gap-5 py-28">
      <h1 className="font-display text-4xl font-extrabold tracking-tight">Esta página no está disponible</h1>
      <p className="text-lg text-ink-soft">Puede que la vacante ya se haya cerrado. Revise las vacantes activas.</p>
      <ButtonLink href="/#vacantes">Ver vacantes activas</ButtonLink>
    </Container>
  );
}
