"use client";

import Link from "next/link";
import { useState } from "react";
import type { FinancialResearchReadout } from "../../lib/financial-research-api";
import {
  type BusinessGroup,
  type Chain,
  type CompanyResearchGroup,
  type CompanyResearchViewV2,
  type FinancialItem,
  type FinancialMetric,
  type GrowthFactor,
  type Investment,
  type ResearchGap,
  type ResearchProduct,
  type ResearchSource,
  type RiskFactor,
  type RevenueDataset,
  getOfficialSources,
  getResearchGroup,
  resolveCompetitor,
} from "../../lib/stock-research-preview";

function formatPeriod(period: string | null | undefined, periodType?: string | null): string {
  if (!period) return "期間未載明";
  if (/^FY\d{4}$/.test(period)) return `${period.slice(2)} 全年`;
  if ((periodType === "half_year" || periodType === "ytd") && /^(\d{4})Q2_YTD$/.test(period)) return `${period.slice(0, 4)} 上半年`;
  if ((periodType === "nine_month" || periodType === "ytd") && /^(\d{4})Q3_YTD$/.test(period)) return `${period.slice(0, 4)} 前三季累計`;
  if (/^(\d{4})Q([1-4])_YTD$/.test(period)) return `${period.slice(0, 4)} 年第${period.slice(5, 6)}季累計`;
  if (/^(\d{4})Q([1-4])$/.test(period)) return `${period.slice(0, 4)} 年第${period.slice(5, 6)}季`;
  if (/^(\d{4})-01-01\/\d{4}-06-30$/.test(period)) return `${period.slice(0, 4)} 上半年`;
  if (/^(\d{4})-01-01\/\d{4}-12-31$/.test(period)) return `${period.slice(0, 4)} 全年`;
  if (/^(\d{4})-01-01\/\d{4}-03-31$/.test(period)) return `${period.slice(0, 4)} 第一季`;
  if (/^(\d{4})-04-01\/\d{4}-06-30$/.test(period)) return `${period.slice(0, 4)} 第二季`;
  if (/^(\d{4})-07-01\/\d{4}-09-30$/.test(period)) return `${period.slice(0, 4)} 第三季`;
  if (/^(\d{4})-10-01\/\d{4}-12-31$/.test(period)) return `${period.slice(0, 4)} 第四季`;
  if (/^(\d{4})-Q[1-4]$/.test(period)) return `${period.slice(0, 4)} 第${period.slice(-1)}季`;
  if (/^(\d{4})-H1$/.test(period)) return `${period.slice(0, 4)} 上半年`;
  return period.split("/").map((part) => part.replaceAll("-", "/")).join("–");
}

function formatBasis(value: string | null | undefined): string {
  if (!value) return "財報口徑";
  const normalized = value.replaceAll("/", "_");
  const labels: Record<string, string> = {
    CONSOLIDATED: "合併財報",
    CONSOLIDATED_EXTERNAL_CUSTOMER_REVENUE_BY_BUSINESS_GROUP: "合併外部客戶收入／事業群",
    CONSOLIDATED_SEGMENT_PRETAX_PROFIT_LOSS: "合併部門稅前損益",
    CONSOLIDATED_ATTRIBUTABLE_TO_PARENT: "合併歸屬母公司",
    CONSOLIDATED_BALANCE_SHEET: "合併資產負債表",
    MANAGEMENT_IR_EQUITY_METHOD_INCOME_CHANGE_QOQ: "管理層法說橋接",
    OTHER_INVESTMENT_LOSS: "其他投資損失",
  };
  if (labels[value]) return labels[value];
  if (normalized.includes("EXTERNAL") && normalized.includes("REVENUE")) return "合併外部客戶收入／營運部門";
  if (normalized.includes("SEGMENT") && normalized.includes("PROFIT")) return "合併部門損益";
  if (normalized.includes("MANAGEMENT") || normalized.includes("IR")) return "管理層法說橋接";
  return value.replaceAll("_", "／").replaceAll("/", "／");
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "日期未載明";
  return value.replaceAll("-", "/");
}

function formatAmount(value: number | null | undefined, unit?: string | null, currency?: string | null): string {
  if (value == null || Number.isNaN(value)) return "—";
  const formatted = value.toLocaleString("zh-TW", { maximumFractionDigits: 2 });
  if (unit === "TWD_100_MILLION" || unit === "TWD_100_MILLION_APPROX") return `${formatted} 億元${unit.endsWith("_APPROX") ? "（約）" : ""}`;
  if (unit === "TWD_1000") return `${formatted} 仟元`;
  if (unit === "TWD_PER_SHARE") return `${formatted} 元／股`;
  if (unit === "%") return `${formatted}%`;
  if (currency === "TWD") return `${formatted} 元`;
  return formatted;
}

function formatApiAmount(value: string | number | null, unit: string, currency: string | null): { value: number; unit: string; currency: string | null } | null {
  const numeric = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numeric)) return null;
  if (unit === "BASE_CURRENCY" && currency === "TWD") return { value: numeric / 100_000_000, unit: "TWD_100_MILLION", currency };
  return { value: numeric, unit, currency };
}

const API_METRIC_LABELS: Record<string, string> = {
  revenue: "合併營收",
  gross_profit: "營業毛利",
  gross_profit_reported: "營業毛利（報表）",
  cost_of_revenue: "營業成本",
  operating_expenses: "營業費用",
  operating_income: "營業利益",
  pretax_income: "稅前淨利",
  net_income: "本期淨利",
  parent_net_income: "歸屬母公司淨利",
  assets: "資產總額",
  current_assets: "流動資產",
  non_current_assets: "非流動資產",
  current_liabilities: "流動負債",
  non_current_liabilities: "非流動負債",
  parent_equity: "歸屬母公司權益",
  noncontrolling_interest: "非控制權益",
  cash_and_equivalents: "現金及約當現金",
  cash_from_operations: "營業活動現金流",
  cash_from_investing: "投資活動現金流",
  cash_from_financing: "融資活動現金流",
  cash_at_beginning: "期初現金",
  cash_at_end: "期末現金",
  fx_effect_on_cash: "匯率變動影響",
  net_change_in_cash: "現金淨增加（減少）",
  gross_margin: "毛利率",
  operating_margin: "營業利益率",
  net_margin: "淨利率",
  basic_eps: "基本每股盈餘",
  diluted_eps: "稀釋每股盈餘",
};

function apiStatementLabel(statement: string | null): string {
  if (statement === "balance_sheet") return "資產負債表";
  if (statement === "cash_flow") return "現金流量表";
  if (statement === "derived_income_statement") return "依同期間財報計算";
  return "損益表";
}

function apiFinancialMetrics(readout: FinancialResearchReadout | null | undefined): { metrics: FinancialMetric[]; limited: string[] } {
  const apiMetrics = readout?.summary?.metrics ?? [];
  const metrics: FinancialMetric[] = [];
  const limited: string[] = [];
  apiMetrics.forEach((item) => {
    const display = formatApiAmount(item.value, item.unit, item.currency);
    const label = API_METRIC_LABELS[item.metric] ?? item.metric;
    const period = item.period_label;
    if (item.validation_status !== "PASS") {
      limited.push(`${label}（${formatPeriod(period, item.period_type)}）：${item.validation_note ?? "仍待完成驗證，暫不列入可判讀數值。"}`);
      return;
    }
    if (!display) return;
    metrics.push({
      id: `api-${item.metric}-${period}`,
      label,
      value: display.value,
      unit: display.unit,
      currency: display.currency,
      period,
      periodType: item.statement === "balance_sheet" ? "instant" : "duration",
      reportingBasis: apiStatementLabel(item.statement),
      periodLabelType: item.period_type,
      metricDefinition: item.validation_note ?? "同一期間官方財報科目，已通過 Preview 驗證。",
      status: "AVAILABLE",
    });
  });
  return { metrics, limited: Array.from(new Set(limited)) };
}

function formatMetricValue(metric: FinancialMetric): string {
  return formatAmount(metric.value, metric.unit, metric.currency);
}

function horizonLabel(value: string | null | undefined): string | null {
  if (!value) return null;
  const labels: Record<string, string> = {
    NEAR_TO_MEDIUM: "近中期",
    NEAR_TO_MEDIUM_TERM: "近中期",
    MEDIUM: "中期",
    MEDIUM_TERM: "中期",
    MEDIUM_TO_LONG_TERM: "中長期",
    CYCLICAL: "景氣循環",
    LONG_TERM_PLAN: "長期規劃",
    ONGOING_CYCLICAL: "持續觀察",
    ONGOING: "持續觀察",
  };
  return labels[value] ?? value;
}

function materialityBadges(value: string | null | undefined): string[] {
  if (value === "BOTH") return ["財務影響", "策略重要"];
  if (value === "FINANCIAL") return ["財務影響"];
  if (value === "STRATEGIC") return ["策略重要"];
  return [];
}

function uniqueDatasets(datasets: RevenueDataset[]): RevenueDataset[] {
  const seen = new Set<string>();
  return datasets.filter((dataset) => {
    if (seen.has(dataset.id)) return false;
    seen.add(dataset.id);
    return true;
  });
}

function productsText(products: CompanyResearchGroup["products"]): string | null {
  if (typeof products === "string") return products;
  if (!products?.length) return null;
  return products.map((product) => product.name).join("、");
}

function DataIcon({ symbol, tone = "brown" }: { symbol: string; tone?: string }) {
  return <span className={`tp-company-research-data-icon is-${tone}`} aria-hidden="true">{symbol}</span>;
}

function SectionHeader({ number, title, summary }: { number: string; title: string; summary?: string | null }) {
  return <div className="tp-company-research-section-heading">
    <span className="tp-company-research-section-number">{number}</span>
    <div className="tp-company-research-section-title">
      <h2>{title}</h2>
      {summary && <p>{summary}</p>}
    </div>
  </div>;
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return <div className="tp-company-research-empty"><strong>{title}</strong><p>{description}</p></div>;
}

function TagList({ items, className = "" }: { items?: string[] | null; className?: string }) {
  if (!items?.length) return null;
  return <div className={`tp-company-research-tags ${className}`.trim()}>{items.map((item) => <span key={item}>{item}</span>)}</div>;
}

function CompetitorLinks({ items }: { items?: string[] | null }) {
  if (!items?.length) return <p className="tp-company-research-no-competitors">目前沒有可核對的主要競爭者。</p>;
  return <div className="tp-company-research-competitor-links">{items.map((item) => {
    const competitor = resolveCompetitor(item);
    return competitor.stockId
      ? <Link className="tp-company-research-competitor-link" href={`/stocks/${competitor.stockId}`} key={item}>{competitor.stockId} {competitor.name}<span aria-hidden="true">↗</span></Link>
      : <span className="tp-company-research-competitor-link is-unresolved" title="目前股票主檔無法唯一確認代號" key={item}>{competitor.name}</span>;
  })}</div>;
}

function RevenueDonut({ dataset }: { dataset: RevenueDataset | null }) {
  const eligible = Boolean(dataset?.chartEligible && dataset.items.length && dataset.items.every((item) => typeof item.share === "number"));
  if (!eligible || !dataset) return <EmptyState title="目前尚未提供可繪製的分類營收" description="目前沒有同一期間、同一口徑且具備完整分類比例的收入資料。" />;

  const items = [...dataset.items].sort((left, right) => (right.share ?? 0) - (left.share ?? 0));
  const colorMap: Record<string, string> = {
    "electronic-materials": "#3c78bd",
    "plastic-products": "#ed8564",
    chemical: "#78ac77",
    polyester: "#eab75b",
    other: "#a8a8a8",
  };
  const colors = ["#8a6f58", "#b28d6b", "#6f8874", "#c4a98e", "#aa9a83", "#7e7d70"];
  const stops = items.map((item, index) => {
    const start = items.slice(0, index).reduce((sum, current) => sum + (current.share ?? 0), 0) * 100;
    const end = start + (item.share ?? 0) * 100;
    return `${colorMap[item.businessGroupId ?? item.id] ?? colors[index % colors.length]} ${start}% ${end}%`;
  });

  return <div className="tp-company-research-revenue-chart">
    <div className="tp-company-research-donut" style={{ background: `conic-gradient(${stops.join(", ")})` }} aria-label={`${formatPeriod(dataset.period)}營收結構圖`}>
      <div><span>{formatPeriod(dataset.period)}</span><strong>營收結構</strong></div>
    </div>
    <div className="tp-company-research-revenue-summary">
      <div className="tp-company-research-revenue-total"><span>營收總額</span><strong>{formatAmount(dataset.total, dataset.unit, dataset.currency)}</strong><small>{formatBasis(dataset.reportingBasis)}</small></div>
      <div className="tp-company-research-revenue-legend">
        {items.map((item, index) => <div key={item.id}>
          <span className="tp-company-research-legend-dot" style={{ background: colorMap[item.businessGroupId ?? item.id] ?? colors[index % colors.length] }} />
          <span>{item.name}</span>
          <strong>{((item.share ?? 0) * 100).toFixed(1)}%</strong>
        </div>)}
      </div>
    </div>
  </div>;
}

function OverviewSection({ view }: { view: CompanyResearchViewV2 }) {
  const group = getResearchGroup(view, "company_overview");
  if (!group) return null;
  const fields: Array<[string, string | null | undefined]> = [
    ["營運模式", group.operatingModel],
    ["核心業務", group.coreBusiness],
    ["主要產品與服務", productsText(group.products)],
    ["產業角色", group.industryRole],
  ];
  return <section className="tp-company-research-section tp-company-research-overview-section" id="company-research-overview">
    <SectionHeader number="01" title="公司研究概況" summary="公司定位、營運模式、核心業務與產業角色" />
    <div className="tp-company-research-overview-layout">
      <div className="tp-company-research-positioning tp-company-research-positioning-card">
        <DataIcon symbol="▥" tone="orange" />
        <div><span className="tp-company-research-kicker">公司定位</span><h3>{group.positioning ?? "公司定位尚未提供"}</h3></div>
      </div>
      <div className="tp-company-research-overview-facts">
        {fields.map(([label, value], index) => <div className="tp-company-research-overview-fact-card" key={label}>
          <DataIcon symbol={index === 0 ? "▤" : index === 1 ? "□" : index === 2 ? "▤" : "♧"} tone={index === 3 ? "brown" : index === 1 ? "orange" : "brown"} />
          <div><strong>{label}</strong><p>{value ?? "尚未提供"}</p></div>
        </div>)}
      </div>
    </div>
    <div className="tp-company-research-core-note"><span className="tp-company-research-core-symbol" aria-hidden="true">●</span><strong>研究核心觀察</strong><p>{group.coreObservation ?? "目前尚未整理核心觀察。"}</p></div>
    {group.facts?.length ? <div className="tp-company-research-overview-facts-note"><strong>補充觀察</strong>{group.facts.map((fact) => <p key={fact}>{fact}</p>)}</div> : null}
  </section>;
}

function InvestmentListCard({ investment, onOpen }: { investment: Investment; onOpen: () => void }) {
  const badges = materialityBadges(investment.materiality);
  return <article className="tp-company-research-investment-list-card">
    <DataIcon symbol="≋" tone={investment.materiality === "FINANCIAL" ? "red" : "blue"} />
    <div className="tp-company-research-investment-list-copy"><strong>{investment.name}</strong><span>{investment.stockCode ? `${investment.stockCode} · ` : ""}{investment.relationshipType ?? "轉投資公司"}</span><p>{investment.financialImpact ?? investment.strategicImpact ?? "研究包已整理其與本公司的關係。"}</p></div>
    <div className="tp-company-research-investment-list-action">{badges.map((badge) => <em key={badge}>{badge}</em>)}<button type="button" onClick={onOpen}>查看詳情</button></div>
  </article>;
}

function InvestmentDetail({ investment, limitations, onClose }: { investment: Investment; limitations?: string[]; onClose: () => void }) {
  const fields: Array<[string, string | null]> = [
    ["關係", investment.relationshipType ?? null],
    ["持股比例", typeof investment.holdingPercent === "number" ? `${investment.holdingPercent.toFixed(2)}%` : null],
    ["主要業務", investment.businessDescription ?? null],
    ["財務影響", investment.financialImpact ?? null],
    ["策略意義", investment.strategicImpact ?? null],
    ["會計口徑", investment.accountingTreatment ?? null],
    ["重大性說明", investment.materialityReason ?? null],
  ];
  return <article className="tp-company-research-investment-detail">
    <div className="tp-company-research-investment-detail-heading"><div><span className="tp-company-research-kicker">轉投資詳情</span><h4>{investment.name}</h4></div><button type="button" className="tp-company-research-close" onClick={onClose} aria-label="關閉轉投資詳情">×</button></div>
    <dl>{fields.filter(([, value]) => value).map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    {limitations?.length ? <div className="tp-company-research-investment-limitations"><strong>資料限制</strong>{limitations.map((item) => <p key={item}>{item}</p>)}</div> : null}
  </article>;
}

function BusinessGroupCard({ businessGroup, products, index }: { businessGroup: BusinessGroup; products: ResearchProduct[]; index: number }) {
  const groupProducts = products.filter((product) => product.businessGroupId === businessGroup.id);
  return <article className="tp-company-research-business-group-card">
    <DataIcon symbol={index === 0 ? "◉" : index === 1 ? "♧" : index === 2 ? "⬡" : "□"} tone={index === 0 ? "blue" : index === 1 ? "orange" : index === 2 ? "green" : "brown"} />
    <div><strong>{businessGroup.name}</strong><p>{businessGroup.summary ?? "事業群摘要尚未提供"}</p><small>{groupProducts.map((product) => product.name).join("、") || businessGroup.products?.join("、") || "產品資料尚未提供"}</small></div>
  </article>;
}

function BusinessSection({ view }: { view: CompanyResearchViewV2 }) {
  const group = getResearchGroup(view, "business_structure");
  const [activeInvestmentId, setActiveInvestmentId] = useState<string | null>(null);
  if (!group) return null;
  const businessGroups = group.businessGroups ?? [];
  const products = Array.isArray(group.products) ? group.products : [];
  const full = group.fullResearch?.revenueStructure?.v2;
  const revenueDatasets = uniqueDatasets([...(full?.revenueDatasets ?? []), ...(group.revenue?.datasets ?? [])]);
  const revenue = revenueDatasets.find((dataset) => dataset.chartEligible) ?? revenueDatasets[0] ?? null;
  const investments = group.investments?.items ?? [];
  const activeInvestment = investments.find((investment) => investment.id === activeInvestmentId) ?? null;
  const layoutClass = investments.length ? "" : "without-investments";
  return <section className="tp-company-research-section tp-company-research-business-section" id="company-research-business">
    <SectionHeader number="02" title="產品與營收結構" summary="產品線、事業群、營收結構與重要轉投資" />
    <div className={`tp-company-research-business-layout ${layoutClass}`.trim()}>
      <div className="tp-company-research-revenue-column">
        <div className="tp-company-research-subheading"><div><h3>營收結構</h3><p>{revenue ? `${formatPeriod(revenue.period)} · ${formatBasis(revenue.reportingBasis)}` : "收入分類尚未提供"}</p></div></div>
        <RevenueDonut dataset={revenue} />
        {revenue?.reconciliation && <p className="tp-company-research-caption">{revenue.reconciliation}</p>}
        {revenue?.notes && <p className="tp-company-research-caption">{revenue.notes}</p>}
      </div>
      <div className="tp-company-research-business-groups">
        <div className="tp-company-research-subheading"><div><h3>主要產品與事業群</h3><p>各事業群的產品與主要應用。</p></div></div>
        <div className="tp-company-research-business-group-list">{businessGroups.map((businessGroup, index) => <BusinessGroupCard key={businessGroup.id} businessGroup={businessGroup} products={products} index={index} />)}</div>
      </div>
      {investments.length ? <div className="tp-company-research-investments">
        <div className="tp-company-research-subheading"><div><h3>重要轉投資與獲利影響</h3><p>研究包已整理的財務或策略關係。</p></div></div>
        {activeInvestment ? <InvestmentDetail investment={activeInvestment} limitations={group.investments?.limitations} onClose={() => setActiveInvestmentId(null)} /> : <div className="tp-company-research-investment-list">{investments.map((investment) => <InvestmentListCard key={investment.id} investment={investment} onOpen={() => setActiveInvestmentId(investment.id)} />)}</div>}
      </div> : null}
    </div>
  </section>;
}

function IndustryStage({ label, value, className = "" }: { label: string; value?: string | null; className?: string }) {
  return <div className={`tp-company-research-chain-stage ${className}`.trim()}><span>{label}</span><p>{value ?? "尚未提供"}</p></div>;
}

function IndustryChain({ chain, companyName }: { chain: Chain; companyName: string }) {
  return <div className="tp-company-research-chain-content">
    <div className="tp-company-research-chain-flow">
      <IndustryStage label="上游" value={chain.upstream} />
      <div className="tp-company-research-chain-stage is-company"><span>中游</span><strong>{companyName}的參與描述</strong><p>{chain.companyRole ?? "公司參與描述尚未提供"}</p></div>
      <IndustryStage label="下游" value={chain.downstream} />
    </div>
    <div className={`tp-company-research-competition-grid ${chain.competitors?.length ? "has-competitors" : "without-competitors"}`.trim()}>
      <div><span>競爭優勢</span><TagList className="is-copy" items={chain.competitiveAdvantages} /></div>
      <div><span>競爭限制</span><TagList className="is-copy" items={chain.competitiveConstraints} /></div>
      <div className="tp-company-research-competitors"><span>主要競爭者</span><CompetitorLinks items={chain.competitors} /></div>
    </div>
  </div>;
}

function IndustrySection({ view, companyName }: { view: CompanyResearchViewV2; companyName: string }) {
  const group = getResearchGroup(view, "industry_position");
  const [activeChainId, setActiveChainId] = useState<string | null>(null);
  if (!group) return null;
  const chains = group.chains ?? [];
  const chain = chains.find((item) => item.id === activeChainId) ?? chains[0] ?? null;
  return <section className="tp-company-research-section tp-company-research-industry-section" id="company-research-industry">
    <SectionHeader number="03" title="產業鏈與競爭位置" summary={group.summary} />
    {chains.length > 1 ? <div className="tp-company-research-chain-picker" role="tablist" aria-label="其他產業鏈">{chains.map((item) => <button type="button" role="tab" aria-selected={chain?.id === item.id} className={chain?.id === item.id ? "is-active" : ""} key={item.id} onClick={() => setActiveChainId(item.id)}>{item.name}</button>)}</div> : null}
    {chain ? <IndustryChain chain={chain} companyName={companyName} /> : <EmptyState title="產業鏈資料尚未提供" description="目前沒有可供顯示的產業鏈資料。" />}
    {group.competitivePosition && <p className="tp-company-research-section-note">{group.competitivePosition}</p>}
  </section>;
}

function FactorCard({ item, businessNames, type }: { item: GrowthFactor | RiskFactor; businessNames: Map<string, string>; type: "growth" | "risk" }) {
  const indicators = item.observationIndicators ?? item.indicators ?? [];
  const businesses = (item.affectedBusinesses ?? []).map((id) => businessNames.get(id) ?? id);
  const horizon = horizonLabel(item.timeHorizon ?? item.horizon);
  return <details className={`tp-company-research-factor-card is-${type}`}>
    <summary><span className="tp-company-research-factor-index" /> <span className="tp-company-research-factor-title"><strong>{item.name}</strong>{item.summary && <small>{item.summary}</small>}</span>{horizon && <span className="tp-company-research-factor-horizon">{horizon}</span>}<b aria-hidden="true">›</b></summary>
    <div className="tp-company-research-factor-body">
      {item.mechanism && <div><span>影響機制</span><p>{item.mechanism}</p></div>}
      {businesses.length ? <div><span>涉及業務</span><TagList items={businesses} /></div> : null}
      {indicators.length ? <div><span>後續觀察</span><TagList items={indicators} /></div> : null}
      {horizon && <div><span>觀察期間</span><p>{horizon}</p></div>}
    </div>
  </details>;
}

function FactorColumn({ items, businessNames, type }: { items: Array<GrowthFactor | RiskFactor>; businessNames: Map<string, string>; type: "growth" | "risk" }) {
  return <div className="tp-company-research-factor-list">{items.map((item) => <FactorCard key={item.id} item={item} businessNames={businessNames} type={type} />)}</div>;
}

function GrowthRiskSection({ view }: { view: CompanyResearchViewV2 }) {
  const group = getResearchGroup(view, "growth_and_risks");
  const businessGroup = getResearchGroup(view, "business_structure");
  if (!group) return null;
  const businessNames = new Map((businessGroup?.businessGroups ?? []).map((item) => [item.id, item.name]));
  return <section className="tp-company-research-section tp-company-research-growth-section" id="company-research-growth">
    <SectionHeader number="04" title="成長驅動與主要風險" summary="目前最直接的營運驅動與需要持續觀察的風險" />
    <div className="tp-company-research-growth-risk-grid">
      <div className="tp-company-research-factor-column"><div className="tp-company-research-column-heading"><span className="is-growth">成長驅動</span><strong>{group.growthFactors?.length ?? 0} 項</strong></div><FactorColumn items={group.growthFactors ?? []} businessNames={businessNames} type="growth" /></div>
      <div className="tp-company-research-factor-column"><div className="tp-company-research-column-heading"><span className="is-risk">主要風險</span><strong>{group.riskFactors?.length ?? 0} 項</strong></div><FactorColumn items={group.riskFactors ?? []} businessNames={businessNames} type="risk" /></div>
    </div>
  </section>;
}

function periodEnd(period: string | null | undefined): string {
  if (!period) return "";
  if (/^FY\d{4}$/.test(period)) return `${period.slice(2)}-12-31`;
  const quarterEnd = { "1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31" } as const;
  if (/^(\d{4})Q([1-4])_YTD$/.test(period)) return `${period.slice(0, 4)}-${quarterEnd[period.slice(5, 6) as keyof typeof quarterEnd]}`;
  if (/^(\d{4})Q([1-4])$/.test(period)) return `${period.slice(0, 4)}-${quarterEnd[period.slice(5, 6) as keyof typeof quarterEnd]}`;
  if (/^(\d{4})-H1$/.test(period)) return `${period.slice(0, 4)}-06-30`;
  if (/^(\d{4})-Q1$/.test(period)) return `${period.slice(0, 4)}-03-31`;
  if (/^(\d{4})-Q2$/.test(period)) return `${period.slice(0, 4)}-06-30`;
  if (/^(\d{4})-Q3$/.test(period)) return `${period.slice(0, 4)}-09-30`;
  if (/^(\d{4})-Q4$/.test(period)) return `${period.slice(0, 4)}-12-31`;
  return period.split("/").at(-1) ?? period;
}

function periodKind(period: string): number {
  if (/_YTD$/.test(period)) return 3;
  if (/^FY\d{4}$/.test(period)) return 1;
  if (/-H\d$/.test(period) || /01-01\/\d{4}-06-30$/.test(period)) return 3;
  if (period.includes("/") || /-Q\d$/.test(period)) return 2;
  return 1;
}

function sortPeriods(periods: string[]): string[] {
  return [...new Set(periods)].sort((left, right) => periodEnd(right).localeCompare(periodEnd(left)) || periodKind(right) - periodKind(left) || right.localeCompare(left));
}

function metricPriority(metric: FinancialMetric): number {
  const label = metric.label;
  if (label.includes("合併營收") || label.includes("營業收入")) return 0;
  if (label.includes("營業利益")) return 1;
  if (label.includes("歸屬母公司")) return 2;
  if (label.includes("每股盈餘") || label.includes("EPS")) return 3;
  if (label.includes("稅前")) return 4;
  if (label.includes("淨利")) return 5;
  return 10;
}

function latestPrimaryMetrics(metrics: FinancialMetric[]): FinancialMetric[] {
  const regular = metrics.filter((metric) => metric.type !== "MANAGEMENT");
  const latestPeriod = sortPeriods(regular.map((metric) => metric.period).filter((period): period is string => Boolean(period)))[0];
  if (!latestPeriod) return regular.slice(0, 4);
  return regular.filter((metric) => metric.period === latestPeriod).sort((left, right) => metricPriority(left) - metricPriority(right)).slice(0, 4);
}

function FinancialHighlights({ metrics }: { metrics: FinancialMetric[] }) {
  if (!metrics.length) return <EmptyState title="目前沒有可直接呈現的財務指標" description="研究包尚未整理出可在此區塊呈現的數值。" />;
  return <div className="tp-company-research-financial-highlights">{metrics.map((metric) => <article className="tp-company-research-metric is-primary" key={metric.id}>
    <span>{metric.label}</span><strong className={metric.value < 0 ? "is-negative" : ""}>{formatMetricValue(metric)}</strong><small>{formatPeriod(metric.period, metric.periodLabelType)} · {formatBasis(metric.reportingBasis)}</small>
  </article>)}</div>;
}

function FinancialComparison({ metrics, excludedIds }: { metrics: FinancialMetric[]; excludedIds: Set<string> }) {
  const comparison = metrics.filter((metric) => metric.type !== "MANAGEMENT" && !excludedIds.has(metric.id));
  if (!comparison.length) return null;
  const periods = sortPeriods(comparison.map((metric) => metric.period).filter((period): period is string => Boolean(period)));
  const periodTypes = new Map(comparison.filter((metric) => metric.period).map((metric) => [metric.period as string, metric.periodLabelType]));
  const rowMap = new Map<string, string>();
  comparison.forEach((metric) => rowMap.set(`${metric.label}|${formatBasis(metric.reportingBasis)}`, metric.label));
  const rows = Array.from(rowMap.entries());
  return <div className="tp-company-research-financial-comparison">
    <div className="tp-company-research-subheading"><div><h4>其他財務數據</h4><p>依實際期間與財務口徑排列；缺少的數值不補零。</p></div></div>
    <div className="tp-company-research-table-wrap"><table className="tp-company-research-financial-table"><caption>其他財務數據比較</caption><thead><tr><th scope="col">財務指標</th>{periods.map((period) => <th scope="col" key={period}>{formatPeriod(period, periodTypes.get(period))}</th>)}</tr></thead><tbody>{rows.map(([rowKey, label]) => {
      const basis = rowKey.split("|").slice(1).join("|");
      return <tr key={rowKey}><th scope="row">{label}<small>{basis}</small></th>{periods.map((period) => {
        const metric = comparison.find((item) => item.label === label && formatBasis(item.reportingBasis) === basis && item.period === period);
        return <td key={`${rowKey}-${period}`}>{metric ? <><strong className={metric.value < 0 ? "is-negative" : ""}>{formatMetricValue(metric)}</strong>{metric.metricDefinition && <small>{metric.metricDefinition}</small>}</> : <span className="tp-company-research-missing">—</span>}</td>;
      })}</tr>;
    })}</tbody></table></div>
  </div>;
}

function SpecialMetrics({ metrics }: { metrics: FinancialMetric[] }) {
  if (!metrics.length) return null;
  return <div className="tp-company-research-special-financial"><div className="tp-company-research-subheading"><div><h4>獲利結構補充</h4><p>研究包另列的特殊獲利來源，不與本業營收相加。</p></div></div><div className="tp-company-research-special-metrics">{metrics.map((metric) => <article key={metric.id}><div><strong>{metric.label}</strong><span>{formatPeriod(metric.period)} · {formatBasis(metric.reportingBasis)}</span></div><b className={metric.value < 0 ? "is-negative" : ""}>{formatMetricValue(metric)}</b>{metric.metricDefinition && <p>{metric.metricDefinition}</p>}</article>)}</div></div>;
}

function ProfitDatasets({ datasets, fallback }: { datasets: RevenueDataset[]; fallback?: string | null }) {
  if (!datasets.length) return fallback ? <p className="tp-company-research-financial-narrative">{fallback}</p> : <EmptyState title="部門損益尚未整理" description="目前研究包沒有可直接拆分的部門損益資料。" />;
  return <div className="tp-company-research-profit-datasets">{datasets.map((dataset) => <article className="tp-company-research-profit-dataset" key={dataset.id}>
    <div className="tp-company-research-data-heading"><strong>{dataset.name ?? "部門損益"}</strong><span>{formatPeriod(dataset.period)} · {formatBasis(dataset.reportingBasis)}</span></div>
    {dataset.items.length ? <div className="tp-company-research-profit-grid">{dataset.items.map((item) => <div key={item.id}><span>{item.name}</span><strong className={(item.value ?? 0) < 0 ? "is-negative" : ""}>{formatAmount(item.value, dataset.unit, dataset.currency)}</strong></div>)}</div> : null}
    {dataset.reconciliation && <p className="tp-company-research-caption">{dataset.reconciliation}</p>}
    {dataset.notes && <p className="tp-company-research-caption">{dataset.notes}</p>}
  </article>)}</div>;
}

function FinancialItems({ items }: { items: FinancialItem[] }) {
  if (!items.length) return <p className="tp-company-research-financial-narrative">目前沒有另列的管理層補充內容。</p>;
  return <div className="tp-company-research-financial-items">{items.map((item) => <article key={item.id}><span>{item.type === "ANALYSIS" ? "研究解讀" : "財務資料"}</span><h4>{item.label}</h4><p>{item.summary ?? "尚未提供"}</p></article>)}</div>;
}

function ManagementTopics({ topics }: { topics: NonNullable<CompanyResearchGroup["managementTopics"]> }) {
  if (!topics.length) return <p className="tp-company-research-financial-narrative">目前研究包沒有另列法說會主題。</p>;
  return <div className="tp-company-research-management-list">{topics.map((topic) => <article key={topic.id}><div><strong>{topic.topic}</strong>{topic.statementDate && <span>{formatDate(topic.statementDate)}</span>}</div><p>{topic.summary ?? "尚未提供"}</p></article>)}</div>;
}

function RealFinancialReadiness({ readout, limited }: { readout: FinancialResearchReadout; limited: string[] }) {
  const periods = readout.coverage?.available_periods ?? [];
  const periodTypes = new Map(periods.map((period) => [period.period_label, period.period_type]));
  const periodLabels = sortPeriods(periods.map((period) => period.period_label));
  const prioritizedLimited = [...limited].sort((left, right) => Number(right.includes("8,426,000")) - Number(left.includes("8,426,000")));
  const sourceUrl = "https://mopsov.twse.com.tw/mops/web/ajax_t164sb04";
  return <div className="tp-company-research-real-financial-readiness">
    <div className="tp-company-research-real-financial-heading"><div><span className="tp-company-research-eyebrow">受控 Preview｜官方財報數值</span><h4>可判讀的實際財務資料</h4><p>數值來自官方公開資訊觀測站；尚未進入 Production，也未宣告可公開再分發。</p></div><span className="tp-company-research-real-financial-badge">唯讀</span></div>
    <div className="tp-company-research-real-financial-periods"><strong>目前可用期間</strong>{periodLabels.length ? periodLabels.map((period) => <span key={period}>{formatPeriod(period, periodTypes.get(period))}</span>) : <em>尚無可用期間</em>}</div>
    {limited.length ? <div className="tp-company-research-real-financial-limited"><strong>暫不列入可判讀數值</strong><ul>{prioritizedLimited.slice(0, 6).map((item) => <li key={item}>{item}</li>)}</ul>{limited.length > 6 && <span>另有 {limited.length - 6} 項待驗證科目。</span>}</div> : null}
    <details className="tp-company-research-real-financial-source"><summary>資料來源與顯示限制</summary><p>來源：<a href={sourceUrl} target="_blank" rel="noreferrer">公開資訊觀測站 MOPS 官方入口</a>。本 Preview 保留官方期間、單位與驗證狀態；來源權利目前為待確認，因此不代表已經核准公開發布。</p><p>管理層法說會、部門損益與研究解讀仍在下方分區呈現，不與官方財報數值混用。</p></details>
  </div>;
}

function FinancialApiStatusNote({ readout }: { readout?: FinancialResearchReadout | null }) {
  if (!readout || readout.source === "unavailable") {
    return <p className="tp-company-research-financial-source-note is-limited">目前 Preview 尚未接入官方財報唯讀數值；下方保留研究包內容，未視為正式財務發布。</p>;
  }
  if (readout.status === "AVAILABLE") {
    return <p className="tp-company-research-financial-source-note is-available">受控 Preview 已接入官方財報數值；尚未公開發布，且不會在此階段改動正式題材或 Production 資料。</p>;
  }
  if (readout.status === "BLOCKED_RIGHTS") {
    return <p className="tp-company-research-financial-source-note is-limited">官方財務資料已取得，但公開數值仍待來源權利確認。</p>;
  }
  return <p className="tp-company-research-financial-source-note">正式財務資料目前尚未完成公開 read model；本區保留已整理的研究包內容，不以缺值補零。</p>;
}

function EpsBridgeReadout({ readout }: { readout?: FinancialResearchReadout | null }) {
  const bridge = readout?.epsBridge;
  if (!bridge || bridge.status === "MISSING" || !bridge.records.length) return null;
  const label: Record<string, string> = {
    RECOMPUTED_MATCH: "重算相符",
    RECOMPUTED_MISMATCH: "重算不一致",
    SOURCE_NOTE_AVAILABLE_NOT_INGESTED: "股數尚未接入",
    SOURCE_NOTE_MISSING: "尚缺股數來源",
    SOURCE_NOTE_NOT_FOUND: "尚未找到同期間股數欄位",
    SHARE_UNIT_MISMATCH: "股數單位不一致",
    BRIDGE_INPUT_INCOMPLETE: "橋接資料不足",
    DERIVED_SHARES_PENDING_VALIDATION: "推導股數待驗證",
    PERIOD_MISMATCH: "期間不一致",
  };
  return <div className="tp-company-research-real-financial-limited" data-eps-bridge-status={bridge.status}>
    <strong>EPS 核對</strong>
    <ul>{bridge.records.slice(0, 6).map((record) => <li key={`${record.ticker}-${record.period_label}`}><span>{formatPeriod(record.period_label, record.period_type)}</span>：{label[record.status] ?? "待審查"}{record.recomputed_basic_eps !== null && record.reported_basic_eps !== null ? `（公告 ${record.reported_basic_eps}；重算 ${record.recomputed_basic_eps}）` : ""}</li>)}</ul>
    {bridge.missing_fields.length ? <p>{bridge.missing_fields[0]}</p> : null}
  </div>;
}

function FinancialSection({ view, financialReadout }: { view: CompanyResearchViewV2; financialReadout?: FinancialResearchReadout | null }) {
  const group = getResearchGroup(view, "financial_commentary");
  if (!group) return null;
  const full = group.fullResearch?.revenueStructure;
  const v2 = full?.v2;
  const realReadout = financialReadout?.source === "api" && financialReadout.summary?.status === "AVAILABLE" ? apiFinancialMetrics(financialReadout) : null;
  const metrics = realReadout?.metrics.length ? realReadout.metrics : (group.metrics?.length ? group.metrics : (v2?.financialMetrics ?? []));
  const primaryMetrics = latestPrimaryMetrics(metrics);
  const primaryIds = new Set(primaryMetrics.map((metric) => metric.id));
  const specialMetrics = metrics.filter((metric) => metric.type === "MANAGEMENT");
  const comparisonIds = new Set([...primaryIds, ...specialMetrics.map((metric) => metric.id)]);
  const profitDatasets = uniqueDatasets([...(v2?.profitDatasets ?? []), ...(group.profit?.datasets ?? [])]);
  const lawTopics = group.managementTopics ?? v2?.managementTopics ?? [];
  const managementSummary = typeof v2?.summary === "string" ? v2.summary : v2?.summary?.summary;
  const managementItems = (group.items ?? []).filter((item) => item.type === "ANALYSIS");
  const managementNarratives = [managementSummary, full?.investmentProfitDrivers].filter((item): item is string => Boolean(item));
  const profitFallback = full?.segmentProfit ?? group.profit?.narrative;
  return <section className="tp-company-research-section tp-company-research-financial-section" id="company-research-financial" data-financial-api-status={financialReadout?.status ?? "UNAVAILABLE"} data-financial-api-source={financialReadout?.source ?? "none"} data-financial-api-metrics={String(realReadout?.metrics.length ?? 0)}>
    <SectionHeader number="05" title="財報與法說會補充" summary="公司層級財務重點、部門損益、法說會重點與管理層觀點" />
    <FinancialApiStatusNote readout={financialReadout} />
    {realReadout && financialReadout ? <RealFinancialReadiness readout={financialReadout} limited={realReadout.limited} /> : null}
    <EpsBridgeReadout readout={financialReadout} />
    <div className="tp-company-research-financial-sequence">
      <section className="tp-company-research-financial-block"><div className="tp-company-research-subheading"><div><h3>財務重點</h3><p>先呈現最新報告期間的代表性指標，再以比較表保留其他期間資料。</p></div></div><FinancialHighlights metrics={primaryMetrics} /><FinancialComparison metrics={metrics} excludedIds={comparisonIds} /><SpecialMetrics metrics={specialMetrics} /></section>
      <section className="tp-company-research-financial-block"><div className="tp-company-research-subheading"><div><h3>部門損益</h3><p>部門損益與產品別收入分開閱讀，不從收入占比推算產品獲利。</p></div></div><ProfitDatasets datasets={profitDatasets} fallback={profitFallback} /></section>
      <section className="tp-company-research-financial-block"><div className="tp-company-research-subheading"><div><h3>法說會重點</h3><p>管理層在法說會中說明的營運主題與展望。</p></div></div><ManagementTopics topics={lawTopics} /></section>
      <section className="tp-company-research-financial-block"><div className="tp-company-research-subheading"><div><h3>管理層觀點</h3><p>研究包將管理層說明與研究解讀分開呈現。</p></div></div>{managementNarratives.length ? <div className="tp-company-research-management-narratives">{managementNarratives.map((item) => <p key={item}>{item}</p>)}</div> : null}<FinancialItems items={managementItems} /></section>
    </div>
  </section>;
}

function sourceLabel(source: ResearchSource): string {
  const type = source.type ?? "";
  if (type.includes("ANNUAL")) return "官方年報";
  if (type.includes("FINANCIAL") || type.includes("Q1") || type.includes("Q2")) return "官方財務報告";
  if (type.includes("IR_CONFERENCE") || type.includes("CONFERENCE")) return "官方法人說明會";
  if (type.includes("IR") || source.tier === "P2") return "官方投資人專區";
  if (type.includes("COMPANY_PROFILE")) return "官方公司資料";
  return "官方資料";
}

function gapText(gap: ResearchGap): string {
  return gap.reason ?? "此項資料目前尚未能安全補足。";
}

function SourcesSection({ view }: { view: CompanyResearchViewV2 }) {
  const group = getResearchGroup(view, "sources_and_limitations");
  if (!group) return null;
  const sources = getOfficialSources(view);
  const full = group.fullResearch?.revenueStructure;
  const limitations = [...(group.limitations ?? []), ...(group.gaps ?? []).map(gapText), ...(group.uncertainties ?? []), ...(group.conflicts ?? []), ...(full?.notEstablished ?? []), full?.reason].filter((item, index, all): item is string => Boolean(item) && all.indexOf(item) === index);
  const importantLimitations = limitations.slice(0, 4);
  const otherLimitations = limitations.slice(4);
  return <section className="tp-company-research-section tp-company-research-sources-section" id="company-research-sources">
    <SectionHeader number="06" title="研究來源與資料限制" summary="官方來源、資料期間與目前仍需留意的限制" />
    <div className="tp-company-research-sources-layout">
      <div><div className="tp-company-research-subheading"><div><h3>研究來源</h3><p>前端保留官方網站或交易所官方入口。</p></div></div><div className="tp-company-research-source-list">{sources.length ? sources.map((source) => <a href={source.url ?? undefined} target="_blank" rel="noreferrer" key={source.id}><span>{sourceLabel(source)}</span><strong>{formatDate(source.documentDate ?? source.publishedAt)}</strong><small>{source.publisher ?? "官方發布單位"}</small></a>) : <EmptyState title="目前尚未整理來源連結" description="研究包沒有可公開顯示的官方連結。" />}</div></div>
      <div className="tp-company-research-limitations"><div className="tp-company-research-subheading"><div><h3>資料限制與缺口</h3><p>限制直接影響研究解讀，不代表公司沒有該項業務。</p></div></div>{importantLimitations.length ? <ul>{importantLimitations.map((item) => <li key={item}>{item}</li>)}</ul> : <p>目前沒有額外資料限制。</p>}{otherLimitations.length ? <details className="tp-company-research-other-limitations"><summary>顯示其他限制（{otherLimitations.length}）</summary><ul>{otherLimitations.map((item) => <li key={item}>{item}</li>)}</ul></details> : null}</div>
    </div>
  </section>;
}

function ResearchPublicationNote({ view }: { view: CompanyResearchViewV2 }) {
  if ((view.publicationStatus ?? "").toUpperCase() === "PUBLISHED") return null;
  return <div className="tp-company-research-publication-note" role="status"><strong>研究內容目前為 Preview 審閱版</strong><span>尚未正式發布，內容僅供本次研究審閱，不代表已核准的公開研究。</span></div>;
}

export function StockResearchCards({ companyName, research, financialReadout }: { companyName: string; research?: CompanyResearchViewV2 | null; financialReadout?: FinancialResearchReadout | null }) {
  if (!research) return <div className="tp-company-research-shell"><EmptyState title="公司研究資料尚未提供" description="目前沒有可供此個股顯示的研究資料。" /></div>;
  return <div className="tp-company-research-shell" data-research-code={research.stock.code}>
    <ResearchPublicationNote view={research} />
    <OverviewSection view={research} />
    <BusinessSection view={research} />
    <IndustrySection view={research} companyName={companyName} />
    <GrowthRiskSection view={research} />
    <FinancialSection view={research} financialReadout={financialReadout} />
    <SourcesSection view={research} />
  </div>;
}
