import type { MetadataRoute } from "next";
import { listarVacantes } from "@/lib/api";
import { SITE } from "@/lib/site";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const vacantes = await listarVacantes();
  return [
    { url: SITE.url, changeFrequency: "weekly", priority: 1 },
    ...vacantes.map((v) => ({
      url: `${SITE.url}/vacantes/${v.slug}`,
      lastModified: v.publicada_en,
      changeFrequency: "daily" as const,
      priority: 0.8,
    })),
  ];
}
