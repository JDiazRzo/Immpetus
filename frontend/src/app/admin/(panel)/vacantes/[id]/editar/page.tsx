import { VacancyFormPage } from "@/components/admin/views/VacancyForm";

export default async function Page(props: PageProps<"/admin/vacantes/[id]/editar">) {
  const { id } = await props.params;
  return <VacancyFormPage id={id} />;
}
