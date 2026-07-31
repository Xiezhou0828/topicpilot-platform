import type { StockView } from "../lib/types";

export type LampState = "positive" | "negative" | "neutral" | "missing";

export function classifyLamp({ positive, negative, hasData }: { positive: boolean; negative: boolean; hasData: boolean }): LampState {
  if (!hasData) return "missing";
  if (negative) return "negative";
  if (positive) return "positive";
  return "neutral";
}

const stateText: Record<LampState, string> = {
  positive: "正向訊號",
  negative: "風險訊號",
  neutral: "有資料但未觸發",
  missing: "資料不足",
};

function Lamp({ label, short, state }: { label: string; short: string; state: LampState }) {
  return <span aria-label={`${label}：${stateText[state]}`} className={`signalLamp ${state}`} data-state={state} title={`${label}：${stateText[state]}`}><b>{short}</b><span className="srOnly">{stateText[state]}</span></span>;
}

export function StockSignalLamps({ stock }: { stock: StockView }) {
  const row = stock.watch;
  const chipText = `${row?.fundingConfirm ?? ""} ${row?.shortRisk ?? ""}`;
  const chipHasData = Boolean(stock.screener.institutionalAsOf || stock.screener.tdccAsOf) && !stock.screener.chipDataGap;
  const chipState = classifyLamp({
    positive: Boolean(row?.hasFunding),
    negative: /籌碼|法人|外資|投信|大戶/.test(chipText) && /賣超|減少|轉弱|風險|背離/.test(chipText),
    hasData: chipHasData,
  });
  const fundamentalText = row?.fundamentalCatalyst ?? "";
  const fundamentalState = classifyLamp({
    positive: Boolean(row?.hasCatalyst),
    negative: /衰退|轉弱|下滑|負成長/.test(fundamentalText),
    hasData: Boolean(stock.fundamental.asOf),
  });
  const riskText = row?.shortRisk ?? stock.riskNote ?? "";
  const riskState = classifyLamp({
    positive: false,
    negative: Boolean(row?.hasRisk) || Boolean(riskText && !/暫無|無明顯/.test(riskText)),
    hasData: Boolean(riskText || row),
  });

  return <span className="signalLamps" aria-label="判讀燈號"><Lamp label="籌碼動向" short="籌" state={chipState} /><Lamp label="營運動能" short="營" state={fundamentalState} /><Lamp label="短線風險" short="險" state={riskState} /></span>;
}
