// WEB-DATA-STALE-001（TASK I）：以「台灣交易日」判斷資料是否過期的集中邏輯。
// 純函式、無 UI、無 React；同時供前端與 node --test 使用。
// 原則：
//   - 報價/技術：依台灣交易日判斷是否落後最近交易日。
//   - 法人：依自身日期判斷（允許 T+1~T+2）。
//   - TDCC 大戶（週資料）/ 基本面（月資料）：只顯示日期，不因制度性延遲誤判為報價過期。
//   - 週末/休市日不得製造假警報；缺日期或格式錯誤要安全回傳，不丟例外。
//   - 僅影響提示，不影響任何選股分數 / Gate / 排序。

export const TAIPEI_TIMEZONE = "Asia/Taipei";

// 過期門檻（集中定義、可測試）。單位：交易日。
export const STALE_THRESHOLDS = {
  quoteTradingDays: 1, // 報價/技術落後最近交易日 >= 1 個交易日 → 提示
  institutionalTradingDays: 2, // 法人允許 T+1~T+2，>= 2 才提示
};

function pad2(n) {
  return String(n).padStart(2, "0");
}

export function toISO(date) {
  return `${date.getUTCFullYear()}-${pad2(date.getUTCMonth() + 1)}-${pad2(date.getUTCDate())}`;
}

// 解析純日期。接受 Date、"YYYY-MM-DD"、"YYYYMMDD"；其餘（含月資料 "YYYYMM"、null、亂碼）回 null。
export function parseDateOnly(input) {
  if (input instanceof Date) {
    return Number.isNaN(input.getTime())
      ? null
      : new Date(Date.UTC(input.getUTCFullYear(), input.getUTCMonth(), input.getUTCDate()));
  }
  if (typeof input !== "string") return null;
  const s = input.trim();
  let y;
  let m;
  let d;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
    [y, m, d] = s.split("-").map(Number);
  } else if (/^\d{8}$/.test(s)) {
    y = Number(s.slice(0, 4));
    m = Number(s.slice(4, 6));
    d = Number(s.slice(6, 8));
  } else {
    return null;
  }
  if (m < 1 || m > 12 || d < 1 || d > 31) return null;
  const date = new Date(Date.UTC(y, m - 1, d));
  // 驗證是真實日期（例如 2 月 30 日會被 Date 進位）。
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) {
    return null;
  }
  return date;
}

export function isWeekend(date) {
  const w = date.getUTCDay();
  return w === 0 || w === 6;
}

export function isTradingDay(date, holidays = new Set()) {
  return !isWeekend(date) && !holidays.has(toISO(date));
}

// 取 <= date 的最近交易日（跳過週末與 holidays）。
export function latestTradingDayOnOrBefore(date, holidays = new Set()) {
  const d = new Date(date.getTime());
  for (let i = 0; i < 30; i += 1) {
    if (isTradingDay(d, holidays)) return d;
    d.setUTCDate(d.getUTCDate() - 1);
  }
  return d;
}

// 計算 (from, to] 之間的交易日數；from >= to 回 0。
export function tradingDaysBetween(from, to, holidays = new Set()) {
  if (from.getTime() >= to.getTime()) return 0;
  let count = 0;
  const d = new Date(from.getTime());
  for (let i = 0; i < 400; i += 1) {
    d.setUTCDate(d.getUTCDate() + 1);
    if (d.getTime() > to.getTime()) break;
    if (isTradingDay(d, holidays)) count += 1;
  }
  return count;
}

// 通用過期評估：某資料日期相對「today」落後幾個交易日。
// 缺日期/格式錯誤 → valid:false、stale:false（安全，不誤報也不炸頁面）。
export function evaluateStaleness({ date, today, thresholdDays, holidays = new Set() }) {
  const d = parseDateOnly(date);
  const t = parseDateOnly(today);
  if (!t) return { valid: false, stale: false, gapTradingDays: null, date: d ? toISO(d) : null, latestTradingDay: null };
  const latest = latestTradingDayOnOrBefore(t, holidays);
  if (!d) return { valid: false, stale: false, gapTradingDays: null, date: null, latestTradingDay: toISO(latest) };
  const gap = tradingDaysBetween(d, latest, holidays);
  return {
    valid: true,
    stale: gap >= thresholdDays,
    gapTradingDays: gap,
    date: toISO(d),
    latestTradingDay: toISO(latest),
  };
}

// 取 Asia/Taipei 當日（YYYY-MM-DD）。用於前端；測試可自行傳 today 覆蓋。
export function taipeiToday(now = new Date()) {
  try {
    return new Intl.DateTimeFormat("en-CA", {
      timeZone: TAIPEI_TIMEZONE,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(now);
  } catch {
    return toISO(new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate())));
  }
}

// 依 Freshness（各來源日期）產生逐項過期提示。
// 回傳 { anyStale, items:[{key,label,date,stale,reason,note}] }。
export function evaluateFreshness(freshness, today, holidays = new Set()) {
  const f = freshness ?? {};
  const quote = evaluateStaleness({
    date: f.dataDate,
    today,
    thresholdDays: STALE_THRESHOLDS.quoteTradingDays,
    holidays,
  });
  const inst = evaluateStaleness({
    date: f.institutionalAsOf,
    today,
    thresholdDays: STALE_THRESHOLDS.institutionalTradingDays,
    holidays,
  });

  const items = [
    {
      key: "quote",
      label: "報價/技術",
      date: quote.date,
      stale: quote.stale,
      reason: quote.stale
        ? `報價/技術最後資料日為 ${quote.date}，可能不是最近交易日（最近交易日約 ${quote.latestTradingDay}）`
        : null,
      note: null,
    },
    {
      key: "institutional",
      label: "法人",
      date: inst.date,
      stale: inst.stale,
      reason: inst.stale
        ? `法人資料日為 ${inst.date}，已落後最近交易日約 ${inst.gapTradingDays} 個交易日`
        : null,
      note: null,
    },
    {
      key: "tdcc",
      label: "TDCC大戶",
      date: parseDateOnly(f.tdccAsOf) ? toISO(parseDateOnly(f.tdccAsOf)) : (f.tdccAsOf ?? null),
      stale: false,
      reason: null,
      note: "週資料，允許制度性延遲",
    },
    {
      key: "fundamental",
      label: "基本面",
      date: f.fundamentalYm ?? null,
      stale: false,
      reason: null,
      note: "月資料，以資料年月為準",
    },
  ];

  return { anyStale: items.some((i) => i.stale), items };
}
