/** Existing Topic Lifecycle V0 vocabulary; this is not a sixth-stage design. */
export const OWNER_LIFECYCLE_STAGES = ["萌芽", "發酵", "主升", "成熟", "衰退"] as const;

export type OwnerLifecycleStage = typeof OWNER_LIFECYCLE_STAGES[number];

export const BACKEND_TO_OWNER_LIFECYCLE_STAGE: Record<string, OwnerLifecycleStage> = {
  SPROUTING: "萌芽",
  FERMENTING: "發酵",
  MAIN_RISE: "主升",
  MATURE: "成熟",
  DECLINING: "衰退",
};

// Retained presentation lineage; these values are never accepted from the
// formal backend stage mapper as a sixth or replacement stage.
export const LEGACY_PRESENTATION_ALIASES = {
  "高檔整理": "成熟",
  "退潮": "衰退",
} as const;

export const LIFECYCLE_AVAILABILITY_STATES = [
  "AVAILABLE",
  "FORMAL_AVAILABLE",
  "SHADOW_AVAILABLE",
  "INSUFFICIENT_DATA",
  "PENDING",
  "PREVIEW",
  "NOT_AVAILABLE",
  "WAITING_FOR_FORMAL_LINEAGE",
  "FAIL_CLOSED",
] as const;

export type LifecycleAvailability = typeof LIFECYCLE_AVAILABILITY_STATES[number];

export function ownerStageFromBackend(stage: string | null | undefined): OwnerLifecycleStage | null {
  return stage ? BACKEND_TO_OWNER_LIFECYCLE_STAGE[stage] ?? null : null;
}
