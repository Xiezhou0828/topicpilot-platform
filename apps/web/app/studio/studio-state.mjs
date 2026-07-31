export function assignmentForCharacter(assignments, characterId) {
  return assignments.find((item) => item.characterId === characterId) ?? null;
}

export function performanceIdentity(modelVersion, strategyVersion, sessionVersion) {
  return `${modelVersion}::${strategyVersion}::${sessionVersion}`;
}

export function selectCustomTopic(value) {
  const topic = value.trim();
  return topic
    ? { topic, state: "WAITING_API", message: "等待模型 API；不會產生模擬回答。" }
    : { topic: "", state: "EMPTY", message: "請先輸入討論假設。" };
}

export function panelAfterCharacterSelect(characterId) {
  return { characterId, tab: "character" };
}
