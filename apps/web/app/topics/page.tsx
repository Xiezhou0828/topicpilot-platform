import TopicCatalogPage from "../components/v2/TopicCatalogPage";

export default async function TopicsPage({ searchParams }: { searchParams: Promise<{ asOf?: string }> }) {
  const { asOf } = await searchParams;
  return <TopicCatalogPage key={asOf ?? "current"} asOf={asOf} />;
}
