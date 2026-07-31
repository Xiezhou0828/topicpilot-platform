"use client";

import { useEffect, useState } from "react";
import { FAVORITES_STORAGE_KEY, normalizeFavoriteCodes } from "../lib/favorites-view.mjs";

function readFavorites() {
  if (typeof window === "undefined") return [];

  try {
    const raw = window.localStorage.getItem(FAVORITES_STORAGE_KEY);
    return raw ? normalizeFavoriteCodes(JSON.parse(raw)) : [];
  } catch {
    return [];
  }
}

function writeFavorites(codes: string[]) {
  window.localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(normalizeFavoriteCodes(codes)));
  window.dispatchEvent(new CustomEvent("topic-pilot-favorites-changed"));
}

export function FavoriteButton({ code }: { code: string }) {
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    const sync = () => setFavorites(readFavorites());
    sync();
    window.addEventListener("topic-pilot-favorites-changed", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("topic-pilot-favorites-changed", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const active = favorites.includes(code);

  function toggle() {
    const next = active ? favorites.filter((item) => item !== code) : [...favorites, code];
    setFavorites(next);
    writeFavorites(next);
  }

  return (
    <button
      aria-label={active ? `從自選移除 ${code}` : `加入自選 ${code}`}
      aria-pressed={active}
      className={`favoriteButton ${active ? "active" : ""}`}
      onClick={toggle}
      title={active ? "從自選移除" : "加入自選"}
      type="button"
    >
      <span aria-hidden="true">{active ? "★" : "☆"}</span>
    </button>
  );
}

export function useFavoriteCodes() {
  return useFavoritesState().codes;
}

export function useFavoritesState() {
  const [favorites, setFavorites] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const sync = () => {
      setFavorites(readFavorites());
      setReady(true);
    };
    sync();
    window.addEventListener("topic-pilot-favorites-changed", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("topic-pilot-favorites-changed", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  return { codes: favorites, ready };
}
