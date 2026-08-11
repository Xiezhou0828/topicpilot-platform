"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  buildBundleFromRaw,
  DEMO_FALLBACK_ENABLED,
  fetchRawPublishedSnapshot,
  getBundledBundle,
  getUnavailableBundle,
  getSnapshotApiUrl,
  loadSnapshotApiUrl,
  SnapshotApiError,
} from "./data-source";
import {
  evaluateLiveData,
  isTaiwanMarketSession,
  LIVE_REFRESH_INTERVAL_MS,
  type LiveDataState,
} from "./live-data.mjs";
import type { SnapshotBundle } from "./types";

type RefreshReason = "initial" | "manual" | "interval" | "focus" | "visible";

export type RefreshState = {
  state: "idle" | "loading" | "ok" | "error";
  dataState: LiveDataState;
  message: string | null;
  updatedAt: string | null;
  lastSuccessAt: string | null;
  delayedTradingDays: number | null;
};

export type SnapshotContextValue = {
  bundle: SnapshotBundle;
  status: RefreshState;
  refresh: (reason?: RefreshReason) => Promise<void>;
};

function statusForBundle(bundle: SnapshotBundle): RefreshState {
  const freshness = bundle.qualityPanelData.freshness;
  if (freshness.sourceLabel === "公開合成資料" && DEMO_FALLBACK_ENABLED) {
    return {
      state: "idle",
      dataState: "SNAPSHOT",
      message: "公開作品使用合成資料展示原版介面與企業資料管線，不提供交易判讀。",
      updatedAt: freshness.generatedAt,
      lastSuccessAt: null,
      delayedTradingDays: null,
    };
  }
  const evaluated = evaluateLiveData({
    source: bundle.source,
    dataDate: freshness.dataDate,
    generatedAt: freshness.generatedAt,
    quoteUpdatedAt: freshness.quoteUpdatedAt,
    quoteStatus: freshness.quoteStatus,
    latestTradingDate: freshness.latestTradingDate,
    marketSession: freshness.marketSession,
    rowCount: Math.max(bundle.watchlistData.rows.length, bundle.stockUniverse.length),
  });
  if (!getSnapshotApiUrl()) {
    return {
      state: "idle",
      dataState: "UNAVAILABLE",
      message: "尚未設定獨立 snapshot API，暫不提供交易判斷。",
      updatedAt: freshness.generatedAt,
      lastSuccessAt: null,
      delayedTradingDays: null,
    };
  }
  return {
    state: "idle",
    dataState: evaluated.state,
    message: evaluated.message,
    updatedAt: freshness.generatedAt,
    lastSuccessAt: null,
    delayedTradingDays: evaluated.delayedTradingDays,
  };
}

const fallbackBundle = getBundledBundle();
const fallbackStatus = statusForBundle(fallbackBundle);

const SnapshotContext = createContext<SnapshotContextValue>({
  bundle: fallbackBundle,
  status: fallbackStatus,
  refresh: async () => {},
});

export function SnapshotProvider({ children }: { children: ReactNode }) {
  const initialBundle = getSnapshotApiUrl() || DEMO_FALLBACK_ENABLED ? getBundledBundle() : getUnavailableBundle();
  const [bundle, setBundle] = useState<SnapshotBundle>(() => initialBundle);
  const [status, setStatus] = useState<RefreshState>(() => statusForBundle(initialBundle));
  const requestRef = useRef<Promise<void> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(false);

  const refresh = useCallback((reason: RefreshReason = "manual") => {
    if (requestRef.current) return requestRef.current;

    const controller = new AbortController();
    abortRef.current = controller;
    const timeout = window.setTimeout(() => controller.abort("timeout"), 75_000);

    setStatus((previous) => ({
      ...previous,
      state: "loading",
      dataState: "LOADING",
      message: reason === "manual" ? "正在向後台取得最新資料。" : "正在同步後台報價。",
    }));

    const task = (async () => {
      try {
        const raw = await fetchRawPublishedSnapshot(undefined, controller.signal);
        if (!mountedRef.current) return;
        if (!raw) {
          const fallback = DEMO_FALLBACK_ENABLED ? getBundledBundle() : getUnavailableBundle();
          setBundle(fallback);
          setStatus({ ...statusForBundle(fallback), state: DEMO_FALLBACK_ENABLED ? "ok" : "error" });
          return;
        }

        const next = buildBundleFromRaw(raw);
        const evaluated = evaluateLiveData({
          source: next.source,
          dataDate: next.qualityPanelData.freshness.dataDate,
          generatedAt: next.qualityPanelData.freshness.generatedAt,
          quoteUpdatedAt: next.qualityPanelData.freshness.quoteUpdatedAt,
          quoteStatus: next.qualityPanelData.freshness.quoteStatus,
          latestTradingDate: next.qualityPanelData.freshness.latestTradingDate,
          marketSession: next.qualityPanelData.freshness.marketSession,
          rowCount: Math.max(next.watchlistData.rows.length, next.stockUniverse.length),
        });
        setBundle(next);
        const nextStatus = statusForBundle(next);
        setStatus(next.qualityPanelData.freshness.sourceLabel === "公開合成資料"
          ? { ...nextStatus, state: "ok", lastSuccessAt: new Date().toISOString() }
          : {
              state: "ok",
              dataState: evaluated.state,
              message: evaluated.message,
              updatedAt: next.qualityPanelData.freshness.generatedAt,
              lastSuccessAt: new Date().toISOString(),
              delayedTradingDays: evaluated.delayedTradingDays,
            });
      } catch (error) {
        if (!mountedRef.current || controller.signal.aborted && controller.signal.reason !== "timeout") return;
        const fallback = DEMO_FALLBACK_ENABLED ? getBundledBundle() : getUnavailableBundle();
        setBundle(fallback);
        if (DEMO_FALLBACK_ENABLED) {
          setStatus({
            ...statusForBundle(fallback),
            state: "ok",
            message: controller.signal.reason === "timeout"
              ? "FastAPI 仍在喚醒，先顯示公開合成資料；系統稍後會自動重試。"
              : "FastAPI 暫時無法連線，先顯示公開合成資料。",
          });
        } else {
          setStatus((previous) => ({
            ...previous,
            state: "error",
            dataState: error instanceof SnapshotApiError && error.code === "API_URL_NOT_CONFIGURED"
              ? "UNAVAILABLE"
              : "ERROR",
            message: controller.signal.reason === "timeout"
              ? "FastAPI 連線逾時，暫不提供資料。"
              : error instanceof SnapshotApiError
                ? error.message
                : "無法讀取 FastAPI 資料。",
          }));
        }
      } finally {
        window.clearTimeout(timeout);
        if (abortRef.current === controller) {
          requestRef.current = null;
          abortRef.current = null;
        }
      }
    })();

    requestRef.current = task;
    return task;
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    void loadSnapshotApiUrl().then((url) => {
      if (url) void refresh("initial");
    });

    const onFocus = () => {
      if (getSnapshotApiUrl()) void refresh("focus");
    };
    const onVisibility = () => {
      if (document.visibilityState === "hidden") return;
      if (getSnapshotApiUrl()) void refresh("visible");
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort("unmount");
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [refresh]);

  useEffect(() => {
    const marketSession = bundle.qualityPanelData.freshness.marketSession;
    const interval = window.setInterval(() => {
      const marketIsOpen = marketSession ? marketSession === "OPEN" : isTaiwanMarketSession();
      if (document.visibilityState === "visible" && marketIsOpen && getSnapshotApiUrl()) void refresh("interval");
    }, LIVE_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(interval);
  }, [bundle.qualityPanelData.freshness.marketSession, refresh]);

  const value = useMemo<SnapshotContextValue>(
    () => ({ bundle, status, refresh }),
    [bundle, status, refresh],
  );

  return <SnapshotContext.Provider value={value}>{children}</SnapshotContext.Provider>;
}

export function useSnapshot(): SnapshotContextValue {
  return useContext(SnapshotContext);
}

export function useHomeData() {
  return useContext(SnapshotContext).bundle.homeData;
}

export function useWatchlistData() {
  return useContext(SnapshotContext).bundle.watchlistData;
}

export function useQualityPanel() {
  const context = useContext(SnapshotContext);
  return { data: context.bundle.qualityPanelData, status: context.status, refresh: context.refresh };
}
