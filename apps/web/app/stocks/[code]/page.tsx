import StockDetailRoute from "../../components/v2/StockDetailRoute";

export default async function StockDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <StockDetailRoute code={code} />;
}
