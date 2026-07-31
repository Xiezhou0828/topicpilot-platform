import type { Metadata } from "next";
import { StockDetailView } from "../../views/StockDetailView";

export const metadata: Metadata = { title: "個股資料輪廓" };

export default async function StockDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <StockDetailView code={code} />;
}
