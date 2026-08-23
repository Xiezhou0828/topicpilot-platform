"use client";

import { useEffect, useState } from "react";
import {
  fetchFormalStockHistory,
  type StockHistoryPoint,
  type StockHistoryRead,
} from "../../lib/stock-api";

type HistoryStatus = "LOADING" | "AVAILABLE" | "EMPTY" | "UNAVAILABLE" | "ERROR";

type HistoryState = {
  requestKey: string;
  status: HistoryStatus;
  data: StockHistoryRead | null;
  error: string | null;
};

const EMPTY_VALUE = "—";

function formatNumber(value: number | null | undefined): string {
  return typeof value === "number"
    ? value.toLocaleString("zh-TW", { maximumFractionDigits: 4 })
    : EMPTY_VALUE;
}

function formatDateTime(value: string | null | undefined): string {
  return value ?? EMPTY_VALUE;
}

function historyStatus(data: StockHistoryRead): HistoryStatus {
  return data.items.length === 0 || data.coverageState === "EMPTY" ? "EMPTY" : "AVAILABLE";
}

function LineageFacts({ point }: { point: StockHistoryPoint | null }) {
  return <dl className="tp-stock-history-facts">
    <div><dt>Source</dt><dd>{point?.sourceCode ?? EMPTY_VALUE}</dd></div>
    <div><dt>Adapter</dt><dd>{point?.source?.adapterVersion ?? point?.adapterVersion ?? EMPTY_VALUE}</dd></div>
    <div><dt>Normalization</dt><dd>{point?.source?.normalizationContractVersion ?? point?.normalizationContractVersion ?? EMPTY_VALUE}</dd></div>
    <div><dt>Mapping</dt><dd>{point?.source?.mappingPolicyVersion ?? point?.mappingPolicyVersion ?? EMPTY_VALUE}</dd></div>
    <div><dt>Reference data</dt><dd>{point?.source?.referenceDataVersion ?? point?.referenceDataVersion ?? EMPTY_VALUE}</dd></div>
  </dl>;
}

function HistoryTable({ items }: { items: StockHistoryPoint[] }) {
  return <div className="tp-stock-history-table-wrap">
    <table className="tp-stock-history-table">
      <caption>Raw observed daily price history</caption>
      <thead><tr><th scope="col">Date</th><th scope="col">Open</th><th scope="col">High</th><th scope="col">Low</th><th scope="col">Close</th><th scope="col">Volume</th></tr></thead>
      <tbody>{items.map((point) => <tr key={`${point.tradingDate}-${point.observedAt}`}>
        <th scope="row">{point.tradingDate}</th>
        <td>{formatNumber(point.open)}</td>
        <td>{formatNumber(point.high)}</td>
        <td>{formatNumber(point.low)}</td>
        <td>{formatNumber(point.close)}</td>
        <td>{formatNumber(point.volume)}</td>
      </tr>)}</tbody>
    </table>
  </div>;
}

export function StockPriceHistoryPanel({
  symbol,
  market,
  isPreview = false,
}: {
  symbol: string;
  market?: string | null;
  isPreview?: boolean;
}) {
  const requestKey = `${symbol}|${market ?? ""}|${isPreview ? "preview" : "formal"}`;
  const [state, setState] = useState<HistoryState>({ requestKey, status: isPreview ? "UNAVAILABLE" : "LOADING", data: null, error: null });

  useEffect(() => {
    let active = true;
    const controller = new AbortController();

    if (isPreview) {
      return () => {
        active = false;
        controller.abort();
      };
    }

    fetchFormalStockHistory(symbol, { market, signal: controller.signal }).then((result) => {
      if (!active) return;
      if (result.source === "api" && result.data) {
        setState({ requestKey, status: historyStatus(result.data), data: result.data, error: null });
      } else {
        setState({ requestKey, status: result.state ?? "ERROR", data: null, error: result.error });
      }
    });

    return () => {
      active = false;
      controller.abort();
    };
  }, [isPreview, market, requestKey, symbol]);

  const data = state.requestKey === requestKey ? state.data : null;
  const status = state.requestKey === requestKey ? state.status : isPreview ? "UNAVAILABLE" : "LOADING";
  const firstPoint = data?.items[0] ?? null;
  const adjustmentState = firstPoint?.adjustmentState ?? "UNKNOWN";

  return <section className="tp-stock-encyclopedia-section tp-stock-price-history" data-history-status={status} aria-labelledby="stock-price-history-title">
    <div className="tp-stock-encyclopedia-section-heading"><h3 id="stock-price-history-title">Historical Price / Price History</h3><span>{status}</span></div>
    <p className="tp-stock-history-disclosure">原始交易價格／未套用除權息調整。adjustmentState={adjustmentState}。</p>
    {status === "LOADING" && <p className="tp-stock-encyclopedia-muted">Loading historical price history…</p>}
    {status === "UNAVAILABLE" && <p className="tp-stock-encyclopedia-muted">Historical price history is unavailable. Preview, mock, and legacy data are not used.</p>}
    {status === "ERROR" && <p className="tp-stock-encyclopedia-muted">Historical price history could not be loaded. {state.error ?? "The formal API returned an error."}</p>}
    {status === "EMPTY" && <p className="tp-stock-encyclopedia-muted">No accepted historical price bars are available for the requested period. {data?.availabilityReason ?? ""}</p>}
    {status === "AVAILABLE" && data && <>
      <div className="tp-stock-history-period"><span>Period</span><strong>{data.returnedFrom ?? EMPTY_VALUE} → {data.returnedTo ?? EMPTY_VALUE}</strong><small>{data.pointCount} bars{data.hasMore ? " · bounded result" : ""}</small></div>
      <div className="tp-stock-history-freshness"><span>As of</span><strong>{formatDateTime(data.asOf)}</strong><span>Freshness</span><strong>{data.freshnessState}</strong><span>Latest observed</span><strong>{formatDateTime(data.latestObservedAt)}</strong><span>Latest retrieved</span><strong>{formatDateTime(data.latestRetrievedAt)}</strong></div>
      <LineageFacts point={firstPoint} />
      <HistoryTable items={data.items} />
    </>}
  </section>;
}
