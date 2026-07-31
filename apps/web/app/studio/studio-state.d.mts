import type { AgentAssignment, CharacterId, StudioTab } from "./studio-types";
export function assignmentForCharacter(assignments: AgentAssignment[], characterId: CharacterId): AgentAssignment | null;
export function performanceIdentity(modelVersion: string, strategyVersion: string, sessionVersion: string): string;
export function selectCustomTopic(value: string): { topic: string; state: "WAITING_API" | "EMPTY"; message: string };
export function panelAfterCharacterSelect(characterId: CharacterId): { characterId: CharacterId; tab: StudioTab };
