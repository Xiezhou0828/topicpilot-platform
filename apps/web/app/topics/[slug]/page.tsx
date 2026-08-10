import TopicDetailPage from "../../components/v2/TopicDetailPage";

export default async function TopicDetailRoute({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <TopicDetailPage slug={slug} />;
}
