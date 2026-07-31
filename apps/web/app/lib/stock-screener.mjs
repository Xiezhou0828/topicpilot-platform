export const SCREENER_GROUPS = [
  { id: "trend", label: "趨勢", filters: [
    ["above_ma60", "股價站上 MA60"], ["above_ma20", "股價站上 MA20"], ["ma20_rising", "MA20 向上"],
    ["bullish_alignment", "多頭排列"], ["bullish_structure", "多頭結構"], ["reclaimed_ma20", "剛站回 MA20"],
  ] },
  { id: "momentum", label: "動能／位階", filters: [
    ["rs5_positive", "RS5 > 0"], ["rs20_positive", "RS20 > 0"], ["rs_dual_lead", "RS 雙週期領先"],
    ["near_20d_high", "距 20 日高點 ≤ 3%"], ["breakout_20d_high", "突破 20 日高"],
  ] },
  { id: "oscillator", label: "擺盪時機", filters: [
    ["macd_hist_positive", "MACD 柱翻正"], ["macd_golden_cross", "MACD 黃金交叉"], ["dif_above_zero", "DIF 站上零軸"],
    ["kd_golden_cross", "KD 黃金交叉"], ["kd_low_cross", "KD 低檔黃金交叉"], ["kd_mid_low_cross", "KD 中低檔黃金交叉"],
  ] },
  { id: "volume", label: "量價", filters: [
    ["volume_ratio_12", "量比 ≥ 1.2"], ["healthy_volume", "健康放量（後端狀態）"], ["up_volume_ratio_12", "上漲量比 > 1.2"],
    ["breakout_volume", "突破放量"], ["pullback_shrink", "回檔量縮比 ≤ 0.8"], ["restart_confirmed", "再啟動確認"],
  ] },
  { id: "chip", label: "法人籌碼", filters: [
    ["foreign_streak_3", "外資連買 ≥ 3 日"], ["trust_streak_3", "投信連買 ≥ 3 日"], ["institutions_sync", "法人同步（外資＋投信 5 日皆買超）"],
    ["foreign_buy_3", "外資 5 日買超佔量 ≥ 3%"], ["trust_buy_1", "投信 5 日買超佔量 ≥ 1%"], ["large_holder_up", "大戶增加"],
  ] },
];

const compare = (value, predicate) => value === null || value === undefined ? null : predicate(value);

export function evaluateFilter(stock, id, ranges = {}) {
  const s = stock.screener;
  switch (id) {
    case "above_ma60": return s.close == null || s.ma60 == null ? null : s.close > s.ma60;
    case "above_ma20": return s.close == null || s.ma20 == null ? null : s.close > s.ma20;
    case "ma20_rising": return compare(s.ma20SlopePct, (v) => v > 0);
    case "bullish_alignment": return compare(s.movingAverageAlignment, (v) => v.includes("多頭排列"));
    case "bullish_structure": return compare(s.structureState, (v) => v.includes("多頭結構"));
    case "reclaimed_ma20": return s.reclaimedMa20 ?? compare(s.daysAboveMa20, (v) => v === 1);
    case "rs5_positive": return compare(s.rs5Pct, (v) => v > 0);
    case "rs20_positive": return compare(s.rs20Pct, (v) => v > 0);
    case "rs_dual_lead": return compare(s.rsState, (v) => v.includes("雙週期領先"));
    case "near_20d_high": return compare(s.distanceTo20DayHighPct, (v) => v >= -3 && v <= 3);
    case "breakout_20d_high": return s.breakout20DayHigh ?? null;
    case "macd_hist_positive": return s.macdHistTurnedPositive ?? null;
    case "macd_golden_cross": return s.macdGoldenCross ?? null;
    case "dif_above_zero": return s.difAboveZero ?? null;
    case "kd_golden_cross": return s.kdGoldenCross ?? null;
    case "kd_low_cross": return s.kdLowGoldenCross ?? null;
    case "kd_mid_low_cross": return s.kdMidLowGoldenCross ?? null;
    case "volume_ratio_12": return compare(s.volumeRatio, (v) => v >= 1.2);
    case "healthy_volume": return compare(s.volumeStatus, (v) => v.includes("健康") || v === "正常");
    case "up_volume_ratio_12": return compare(s.upVolumeRatio, (v) => v > 1.2);
    case "breakout_volume": return s.breakoutWithVolume ?? (
      s.breakout20DayHigh == null || s.volumeRatio == null
        ? null
        : s.breakout20DayHigh && s.volumeRatio >= 1.2
    );
    case "pullback_shrink": return compare(s.pullbackVolumeShrinkRatio, (v) => v <= 0.8);
    case "restart_confirmed": return s.restartConfirmed ?? null;
    case "foreign_streak_3": return compare(s.foreignBuyStreakDays, (v) => v >= 3);
    case "trust_streak_3": return compare(s.trustBuyStreakDays, (v) => v >= 3);
    case "institutions_sync": return s.institutionsInSync ?? (
      s.foreignFiveDayBuyPct == null || s.trustFiveDayBuyPct == null
        ? null
        : s.foreignFiveDayBuyPct > 0 && s.trustFiveDayBuyPct > 0
    );
    case "foreign_buy_3": return compare(s.foreignFiveDayBuyPct, (v) => v >= 3);
    case "trust_buy_1": return compare(s.trustFiveDayBuyPct, (v) => v >= 1);
    case "large_holder_up": return compare(s.largeHolderWeeklyChangePp, (v) => v > 0);
    case "rsi_range": return compare(s.rsi14, (v) => (ranges.rsiMin === null || v >= ranges.rsiMin) && (ranges.rsiMax === null || v <= ranges.rsiMax));
    case "price_range": return compare(stock.price, (v) => (ranges.priceMin === null || v >= ranges.priceMin) && (ranges.priceMax === null || v <= ranges.priceMax));
    default: return null;
  }
}

export function evaluateStockFilters(stock, activeIds, mode = "AND", ranges = {}) {
  if (!activeIds.length) return { matches: true, missing: 0 };
  const values = activeIds.map((id) => evaluateFilter(stock, id, ranges));
  const missing = values.filter((value) => value === null).length;
  return {
    matches: mode === "OR"
      ? values.some((value) => value === true)
      : values.every((value) => value === true),
    missing,
  };
}
