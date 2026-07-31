"use client";

import { useCallback, useEffect, useState } from "react";
import { demoFallbackEnabled } from "./api";
import type { DataOrigin } from "./types";

export interface ResourceState<T> {
  data: T | null;
  origin: DataOrigin | null;
  warning: string | null;
  error: Error | null;
  loading: boolean;
  retry: () => void;
}

export function useApiResource<T>(options: {
  key: string;
  load: (signal: AbortSignal) => Promise<T>;
  fallback?: T;
}): ResourceState<T> {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<Omit<ResourceState<T>, "retry">>({
    data: null,
    origin: null,
    warning: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    const controller = new AbortController();
    options.load(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setState({ data, origin: "api", warning: null, error: null, loading: false });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const normalized = error instanceof Error ? error : new Error("發生未預期的資料錯誤。");
        if (demoFallbackEnabled && options.fallback !== undefined) {
          setState({
            data: options.fallback,
            origin: "demo",
            warning: "FastAPI 目前無法連線，已切換至明確標示的合成展示資料。",
            error: null,
            loading: false,
          });
          return;
        }
        setState({ data: null, origin: null, warning: null, error: normalized, loading: false });
      });
    return () => controller.abort();
    // The caller-provided key is the resource identity. Loaders are intentionally
    // captured per key so inline functions do not restart requests on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [options.key, attempt]);

  const retry = useCallback(() => {
    setState((current) => ({ ...current, error: null, loading: true, warning: null }));
    setAttempt((value) => value + 1);
  }, []);
  return { ...state, retry };
}
