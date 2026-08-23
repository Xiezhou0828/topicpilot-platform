"use client";

import { useCallback, useMemo, useSyncExternalStore } from "react";
import {
  FAVORITE_ENTITY_TYPES,
  FAVORITES_CHANGED_EVENT,
  FAVORITES_SCHEMA_VERSION,
  FAVORITES_STORAGE_KEY,
  TOPIC_FAVORITES_STORAGE_KEY,
  createFavoriteIdentity,
  favoriteIdentityMatches,
  normalizeFavoriteIdentities,
  serializeFavoriteIdentities,
  stockCodeFromStableId,
} from "../lib/favorites-view.mjs";

type FavoriteEntityType = "STOCK" | "TOPIC";
type FavoriteToggleOptions = { market?: string | null; displayLabel?: string };
type FavoriteIdentity = {
  version: typeof FAVORITES_SCHEMA_VERSION;
  entityType: FavoriteEntityType;
  stableId: string;
  displayLabel?: string;
};
type FavoriteStoreSnapshot = { ready: boolean; identities: FavoriteIdentity[] };

const EMPTY_SNAPSHOT: FavoriteStoreSnapshot = { ready: false, identities: [] };
const snapshots: Record<FavoriteEntityType, FavoriteStoreSnapshot> = {
  STOCK: EMPTY_SNAPSHOT,
  TOPIC: EMPTY_SNAPSHOT,
};
const subscribers: Record<FavoriteEntityType, Set<() => void>> = {
  STOCK: new Set(),
  TOPIC: new Set(),
};
const storageKeys: Record<FavoriteEntityType, string> = {
  STOCK: FAVORITES_STORAGE_KEY,
  TOPIC: TOPIC_FAVORITES_STORAGE_KEY,
};

function notify(entityType: FavoriteEntityType) {
  subscribers[entityType].forEach((listener) => listener());
}

function readStored(entityType: FavoriteEntityType): FavoriteIdentity[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKeys[entityType]);
    return normalizeFavoriteIdentities(raw ? JSON.parse(raw) : [], entityType) as FavoriteIdentity[];
  } catch {
    // Malformed or unavailable browser storage is a local preference failure,
    // not a reason to block the page or erase the in-memory preference state.
    return [];
  }
}

function hydrate(entityType: FavoriteEntityType) {
  if (typeof window === "undefined" || snapshots[entityType].ready) return;
  snapshots[entityType] = { ready: true, identities: readStored(entityType) };
  notify(entityType);
}

function refresh(entityType: FavoriteEntityType) {
  snapshots[entityType] = { ready: true, identities: readStored(entityType) };
  notify(entityType);
}

function subscribe(entityType: FavoriteEntityType, listener: () => void) {
  if (typeof window === "undefined") return () => undefined;
  subscribers[entityType].add(listener);
  hydrate(entityType);
  const sync = (event: Event) => {
    if (event.type === "storage") {
      const storageEvent = event as StorageEvent;
      if (storageEvent.key !== null && storageEvent.key !== storageKeys[entityType]) return;
    }
    refresh(entityType);
  };
  window.addEventListener(FAVORITES_CHANGED_EVENT, sync);
  window.addEventListener("storage", sync);
  return () => {
    subscribers[entityType].delete(listener);
    window.removeEventListener(FAVORITES_CHANGED_EVENT, sync);
    window.removeEventListener("storage", sync);
  };
}

function getSnapshot(entityType: FavoriteEntityType) {
  return snapshots[entityType];
}

function persist(entityType: FavoriteEntityType, identities: FavoriteIdentity[]) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(storageKeys[entityType], serializeFavoriteIdentities(identities, entityType));
  } catch {
    // Keep the current tab's preference in memory when storage is blocked/full.
  }
  window.dispatchEvent(new CustomEvent(FAVORITES_CHANGED_EVENT, { detail: { entityType } }));
}

function toggleStored(entityType: FavoriteEntityType, identity: FavoriteIdentity) {
  if (typeof window === "undefined") return;
  hydrate(entityType);
  const current = snapshots[entityType].identities;
  const exists = current.some((item) => favoriteIdentityMatches(item, identity));
  const identities = exists
    ? current.filter((item) => !favoriteIdentityMatches(item, identity))
    : [...current, identity];
  snapshots[entityType] = { ready: true, identities };
  notify(entityType);
  persist(entityType, identities);
}

function useFavoriteEntityState(entityType: FavoriteEntityType) {
  const subscribeForEntity = useCallback((listener: () => void) => subscribe(entityType, listener), [entityType]);
  const getSnapshotForEntity = useCallback(() => getSnapshot(entityType), [entityType]);
  const snapshot = useSyncExternalStore(subscribeForEntity, getSnapshotForEntity, () => EMPTY_SNAPSHOT);
  const toggle = useCallback((stableId: string, options: FavoriteToggleOptions = {}) => {
    const identity = createFavoriteIdentity({ entityType, stableId, ...options }) as FavoriteIdentity | null;
    if (identity) toggleStored(entityType, identity);
  }, [entityType]);
  const isFavorite = useCallback((stableId: string, options: FavoriteToggleOptions = {}) => {
    const identity = createFavoriteIdentity({ entityType, stableId, ...options }) as FavoriteIdentity | null;
    return identity ? snapshot.identities.some((item) => favoriteIdentityMatches(item, identity)) : false;
  }, [entityType, snapshot.identities]);
  return { ...snapshot, toggle, isFavorite };
}

export function FavoriteButton({ code, market = null, displayLabel }: { code: string; market?: string | null; displayLabel?: string }) {
  const { ready, isFavorite, toggle } = useFavoritesState();
  const active = isFavorite(code, market);
  return (
    <button
      aria-label={active ? `取消收藏 ${displayLabel ?? code}` : `加入收藏 ${displayLabel ?? code}`}
      aria-pressed={active}
      className={`favoriteButton ${active ? "active" : ""}`}
      disabled={!ready}
      onClick={() => toggle(code, { market, displayLabel })}
      title={active ? "取消收藏" : "加入收藏"}
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
  const state = useFavoriteEntityState(FAVORITE_ENTITY_TYPES.STOCK as FavoriteEntityType);
  const codes = useMemo(() => state.identities.map((identity) => stockCodeFromStableId(identity.stableId)), [state.identities]);
  const isFavorite = useCallback((code: string, market?: string | null) => state.isFavorite(code, { market }), [state.isFavorite]);
  return { ...state, codes, isFavorite };
}

export function useTopicFavoritesState() {
  const state = useFavoriteEntityState(FAVORITE_ENTITY_TYPES.TOPIC as FavoriteEntityType);
  const slugs = useMemo(() => state.identities.map((identity) => identity.stableId), [state.identities]);
  return { ...state, slugs };
}
