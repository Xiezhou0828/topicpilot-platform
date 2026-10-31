"use client";

import { useRouter } from "next/navigation";
import { AppShell, PageContainer } from "./V2Foundation";
import { StockEncyclopediaDrawer, type StockDrawerItem } from "./StockEncyclopediaDrawer";

function stockSeed(code: string): StockDrawerItem {
  return {
    code,
    name: code,
    market: null,
    exchange: null,
    listing: null,
    price: null,
    changePct: null,
    volume: null,
    eod: null,
    updateMode: null,
    dataFreshness: null,
    updatedAt: null,
    dataDate: null,
    topics: [],
    mainTopic: null,
    technicalEvidence: null,
    institutionFlows: null,
    summary: null,
    opportunity: null,
    isPreview: false,
  };
}

export default function StockDetailRoute({ code }: { code: string }) {
  const router = useRouter();
  return <AppShell currentPath="/stocks">
    <PageContainer title="個股研究" hideHeader className="tp-stock-detail-route">
      <StockEncyclopediaDrawer
        stock={stockSeed(code)}
        presentation="page"
        onClose={() => router.push("/stocks")}
      />
    </PageContainer>
  </AppShell>;
}
