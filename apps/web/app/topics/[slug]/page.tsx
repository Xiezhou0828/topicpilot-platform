import TopicCatalogPage from "../../components/v2/TopicCatalogPage";

export default async function TopicDetailRoute({ params, searchParams }: { params: Promise<{ slug: string }>; searchParams: Promise<{ asOf?: string }> }) {
  const { slug } = await params;
  const { asOf } = await searchParams;
  return <TopicCatalogPage key={`${slug}:${asOf ?? "current"}`} slug={slug} asOf={asOf} />;
}
