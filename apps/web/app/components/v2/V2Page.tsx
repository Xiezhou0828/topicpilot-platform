import Link from "next/link";
import { AppShell, Card, DataState, EmptyState, PageContainer } from "./V2Foundation";
import TodayMarketPage from "./TodayMarketPage";
import TopicListPage from "./TopicListPage";

const pageCopy: Record<string, { title: string; description: string; eyebrow: string }> = {
  "/": { eyebrow: "今日市場", title: "今日市場", description: "從市場脈動開始，整理今天值得繼續研究的方向。" },
  "/topics": { eyebrow: "題材探索", title: "題材", description: "查看正在發生的市場題材與後續研究入口。" },
  "/stocks": { eyebrow: "股票資料庫", title: "股票", description: "瀏覽完整股票資料庫，從市場身份開始理解個股。" },
  "/favorites": { eyebrow: "快速存取", title: "收藏", description: "集中查看你想持續追蹤的題材與股票。" },
  "/opportunities": { eyebrow: "研究優先序", title: "機會", description: "整理值得進一步驗證的研究候選。" },
  "/ai-studio": { eyebrow: "深度研究", title: "AI研究室", description: "研究工作區入口，將在後續階段逐步開放。" },
};

export default function V2Page({ path }: { path: string }) {
  if (path === "/") {
    return <AppShell currentPath={path}><TodayMarketPage /></AppShell>;
  }
  if (path === "/topics") return <TopicListPage />;
  const copy = pageCopy[path] ?? pageCopy["/"];
  const title = path === "/opportunities" ? "機會功能尚未發布" : "AI 研究室尚未發布";
  const description = path === "/opportunities" ? "目前沒有正式 Opportunity provider；此頁不會用前端篩選或示範資料產生機會清單。" : "目前沒有可供商用的 AI Research publication；研究示範不會出現在正式產品入口。";
  return <AppShell currentPath={path}><PageContainer eyebrow={copy.eyebrow} title={copy.title} description={copy.description}><Card className="tp-commercial-boundary"><DataState state="UNAVAILABLE" /><EmptyState title={title} description={description} /><p><Link className="tp-button tp-button--secondary" href="/">返回今日市場</Link></p></Card></PageContainer></AppShell>;
}
