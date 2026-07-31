import type { Metadata } from "next";
import { TopicDetailView } from "../../views/TopicDetailView";

export const metadata: Metadata = { title: "題材資料輪廓" };

export default async function TopicDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  return <TopicDetailView slug={slug} />;
}
