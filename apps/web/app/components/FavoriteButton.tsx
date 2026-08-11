"use client";

import { useEffect, useState } from "react";
import { FAVORITES_CHANGED_EVENT, FAVORITES_STORAGE_KEY, TOPIC_FAVORITES_STORAGE_KEY, normalizeFavoriteCodes } from "../lib/favorites-view.mjs";

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
  window.dispatchEvent(new CustomEvent(FAVORITES_CHANGED_EVENT));
}

export function FavoriteButton({ code }: { code: string }) {
  const [favorites, setFavorites] = useState<string[]>([]);

  useEffect(() => {
    const sync = () => setFavorites(readFavorites());
    sync();
    window.addEventListener(FAVORITES_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(FAVORITES_CHANGED_EVENT, sync);
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
    window.addEventListener(FAVORITES_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(FAVORITES_CHANGED_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  function toggle(code: string) {
    const next = favorites.includes(code) ? favorites.filter((item) => item !== code) : [...favorites, code];
    setFavorites(next);
    writeFavorites(next);
  }

  return { codes: favorites, ready, toggle };
}

function readTopicFavorites() {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(TOPIC_FAVORITES_STORAGE_KEY);
    return raw ? normalizeFavoriteCodes(JSON.parse(raw)) : [];
  } catch {
    return [];
  }
}

export function useTopicFavoritesState() {
  const [slugs, setSlugs] = useState<string[]>([]);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const sync = () => { setSlugs(readTopicFavorites()); setReady(true); };
    sync();
    window.addEventListener(FAVORITES_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(FAVORITES_CHANGED_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  function toggle(slug: string) {
    const next = slugs.includes(slug) ? slugs.filter((item) => item !== slug) : [...slugs, slug];
    window.localStorage.setItem(TOPIC_FAVORITES_STORAGE_KEY, JSON.stringify(normalizeFavoriteCodes(next)));
    setSlugs(next);
    window.dispatchEvent(new CustomEvent(FAVORITES_CHANGED_EVENT));
  }

  return { slugs, ready, toggle };
}
