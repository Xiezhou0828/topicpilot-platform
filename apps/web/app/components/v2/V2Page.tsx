import { AppShell, Card, DataState, EmptyState, Freshness, PageContainer, SegmentedControl, Tabs } from "./V2Foundation";
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
  return <AppShell currentPath={path}><PageContainer eyebrow={copy.eyebrow} title={copy.title} description={copy.description}><div className="tp-page-tools"><Freshness /><DataState state="資料待更新" /></div>{path !== "/ai-studio" && <Tabs items={["總覽", "最新變化", "研究清單"]} />}<div className="tp-foundation-grid"><Card><div className="tp-card-heading"><div><p className="tp-overline">Foundation preview</p><h2>{path === "/ai-studio" ? "研究入口已準備" : "內容區域已準備"}</h2></div><SegmentedControl items={["列表", "摘要"]} /></div><EmptyState title="尚未接入頁面資料" description="這是 V2 shared foundation 的 placeholder；本階段不加入商業內容或資料計算。" /></Card><Card className="tp-side-card"><p className="tp-overline">共用資料狀態</p><h2>一致的更新語意</h2><div className="tp-state-list"><DataState state="AVAILABLE" /><DataState state="STALE" /><DataState state="PROVIDER_ERROR" /></div></Card></div></PageContainer></AppShell>;
}
