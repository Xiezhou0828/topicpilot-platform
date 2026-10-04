import type { TopicLifecycle, TopicSummary } from "./topic-api";

export const GRADE_ORDER = ["S", "A", "B", "D"] as const;
export type TopicGrade = (typeof GRADE_ORDER)[number];
export type StrengthView = "ABSOLUTE" | "RELATIVE";

export const GRADE_LABELS: Record<StrengthView, Record<TopicGrade, string>> = {
  ABSOLUTE: { S: "極強", A: "強勢", B: "中性", D: "弱勢" },
  RELATIVE: { S: "大幅領先", A: "領先", B: "接近市場", D: "落後" },
};

export const GRADE_DESCRIPTIONS: Record<TopicGrade, string> = {
  S: "正式分類",
  A: "正式分類",
  B: "正式分類",
  D: "正式分類",
};

export const OVERVIEW_LIFECYCLE_STAGES = ["萌芽", "發酵", "主升", "成熟", "衰退"] as const;
export type OverviewLifecycleStage = (typeof OVERVIEW_LIFECYCLE_STAGES)[number];
export const DETAIL_LIFECYCLE_STAGES = ["尚未形成", ...OVERVIEW_LIFECYCLE_STAGES] as const;
export type DetailLifecycleStage = (typeof DETAIL_LIFECYCLE_STAGES)[number];

export function validGrade(value: string | null | undefined): TopicGrade | null {
  return value === "S" || value === "A" || value === "B" || value === "D" ? value : null;
}

export function gradeLabel(grade: string | null | undefined, view: StrengthView): string | null {
  const normalized = validGrade(grade);
  return normalized ? GRADE_LABELS[view][normalized] : null;
}

export function gradeCopy(grade: string | null | undefined, view: StrengthView): string {
  const normalized = validGrade(grade);
  return normalized ? `${normalized}｜${GRADE_LABELS[view][normalized]}` : "正式分類尚未提供";
}

export function lifecycleStageForOverview(stage: string | null | undefined): OverviewLifecycleStage | null {
  switch (stage) {
    case "SPROUTING": return "萌芽";
    case "FERMENTING": return "發酵";
    case "MAIN_RISE": return "主升";
    case "MATURE": return "成熟";
    case "DECLINING": return "衰退";
    default: return null;
  }
}

export function lifecycleStageForDetail(stage: string | null | undefined): DetailLifecycleStage | null {
  if (stage === "BASE") return "尚未形成";
  return lifecycleStageForOverview(stage);
}

export function lifecycleLabel(stage: DetailLifecycleStage | null): string {
  return stage ?? "生命週期暫不可用";
}

export function isLifecycleRenderable(lifecycle: TopicLifecycle | null | undefined): boolean {
  return Boolean(
    lifecycle &&
    (lifecycle.dataStatus === "AVAILABLE" ||
      lifecycle.dataStatus === "FORMAL_AVAILABLE" ||
      lifecycle.dataStatus === "SHADOW_AVAILABLE") &&
    lifecycleStageForDetail(lifecycle.currentStage) !== null,
  );
}

export function formalRelativeGrade(topic: TopicSummary): string | null {
  return topic.formalStrength?.relative.grade ?? null;
}

export function formalRelativeScore(topic: TopicSummary): number | null {
  return topic.formalStrength?.relative.score ?? null;
}

export function formalAbsoluteScore(topic: TopicSummary): number | null {
  return topic.formalStrength?.absolute.score ?? topic.score;
}

export function formalAbsoluteGrade(topic: TopicSummary): string | null {
  return topic.formalStrength?.absolute.grade ?? topic.grade;
}

export function viewGrade(topic: TopicSummary, view: StrengthView): string | null {
  return view === "ABSOLUTE" ? formalAbsoluteGrade(topic) : formalRelativeGrade(topic);
}

export function viewScore(topic: TopicSummary, view: StrengthView): number | null {
  return view === "ABSOLUTE" ? formalAbsoluteScore(topic) : formalRelativeScore(topic);
}

export function freshnessCopy(topic: TopicSummary): string {
  if (!topic.dataDate) return "正式結果日期尚未提供";
  return `截至 ${topic.dataDate.replace(/-/g, "/")} 盤後`;
}

export function topicHasFormalCurrentState(topic: TopicSummary): boolean {
  return topic.snapshotAvailability === "AVAILABLE" && Boolean(topic.dataDate);
}
