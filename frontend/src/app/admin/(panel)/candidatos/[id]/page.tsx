import { Candidato } from "@/components/admin/views/Candidato";

export default async function Page(props: PageProps<"/admin/candidatos/[id]">) {
  const { id } = await props.params;
  return <Candidato id={id} />;
}
