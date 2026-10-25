import { Container } from "@/components/Container";

export default function Cargando() {
  return (
    <Container className="py-16">
      <div className="h-8 w-2/3 animate-pulse rounded bg-line" />
      <div className="mt-4 h-4 w-1/3 animate-pulse rounded bg-line" />
      <div className="mt-10 h-40 animate-pulse rounded-xl bg-line" />
    </Container>
  );
}
