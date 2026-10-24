import { Convocatoria } from "@/components/admin/views/Convocatoria";

export default async function Page(props: PageProps<"/admin/vacantes/[id]">) {
  const { id } = await props.params;
  return <Convocatoria id={id} />;
}
