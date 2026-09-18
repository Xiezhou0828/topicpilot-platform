"use client";

import { use } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AppShell, PageContainer } from "../../components/v2/V2Foundation";
import { StockEncyclopediaDrawer } from "../../components/v2/StockEncyclopediaDrawer";

export default function StockDetailPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = use(params);
  const market = useSearchParams().get("market");
  const router = useRouter();
  const back = () => { if (window.history.length > 1) router.back(); else router.push("/stocks"); };
  return <AppShell currentPath="/stocks"><PageContainer title="股票詳細資料">
    <nav aria-label="股票導航"><Link href="/stocks">返回股票一覽</Link></nav>
    <StockEncyclopediaDrawer presentation="inline" onClose={back} stock={{
      code, name: code, market, price: null, changePct: null,
      dataFreshness: null, topics: [], isPreview: false,
    }} />
  </PageContainer></AppShell>;
}
