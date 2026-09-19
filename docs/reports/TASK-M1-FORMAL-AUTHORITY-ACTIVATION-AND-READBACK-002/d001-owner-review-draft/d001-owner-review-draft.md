# D001 Owner Review Draft

`STATUS=DRAFT_NOT_FORMAL_AUTHORITY`

This draft was generated under DEC-04=A from the formally approved Structural Role CORE authority. It enumerates candidates only. It does not assign final INCLUDE/EXCLUDE or importance, and it must not be consumed by Score runtime.

## Review contract

- Candidate source: approved Structural Role `CORE` rows only.
- Final membership: Owner-approved `INCLUDED` or `EXCLUDED` per Leaf Topic.
- Importance: current D001 contract permits Owner-approved `1.00`, `0.75`, or `0.50`; these are separate Score-consumer metadata, not automatic Structural Role weights.
- Structural Role mapping: repository evidence does not prove `LEAD -> 1.00`, `CORE -> 0.75`, or `RELATE -> 0.25`; no such mapping is applied.
- Projection bounds: no additional Owner-imposed minimum or maximum; an absent approved projection remains fail closed.
- Empty approved projection: fail closed; never substitute all CORE or Leader Set.
- Ordering: no product-policy meaning; canonical review identifier ascending is used only for deterministic persistence/readback.

## Summary

| Metric | Count |
|---|---:|
| leafTopics | 107 |
| coreCandidateRows | 650 |
| csvRowsIncludingNoCandidateTopicPlaceholders | 651 |
| topicsFullyRecoveredFromExistingHumanAuthority | 0 |
| topicsRequiringOwnerReview | 107 |
| topicsWithNoFormalCoreCandidates | 1 |
| topicsWithExactlyOneCoreCandidate | 11 |
| topicsWithMultipleCoreCandidates | 95 |
| structuralRoleCoreRows | 650 |

`D001_REVIEW_TOPICS=107`  
`D001_REVIEW_CANDIDATES=650`  
`D001_TOPICS_FULLY_RECOVERED_FROM_EXISTING_HUMAN_AUTHORITY=0`  
`D001_TOPICS_REQUIRING_OWNER_REVIEW=107`  
`D001_TOPICS_WITH_NO_CORE_CANDIDATES=1`

## Topics grouped by formal parent

| Parent | Leaf Topic | CORE candidates | Review state | Flags |
|---|---|---:|---|---|
| 晶圓材料 | 12 吋矽晶圓 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 晶圓材料 | 8 吋矽晶圓 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 封裝測試 | ABF載板 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 車用電子 | ADAS | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI運算與伺服器 | AI PCB | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI運算與伺服器 | AI伺服器整機／ODM | 14 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電力與能源 | AI電力基建 | 14 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI視覺 | AI影像辨識 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| IC設計 | ASIC | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI運算與伺服器 | BBU | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 封裝測試 | Chiplet | 13 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 封裝測試 | CoWoS | 8 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 記憶體 | DRAM／DDR | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 封裝測試 | FOPLP | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 晶圓材料 | GaN 晶圓／GaN-on-Si | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 功率半導體 | IGBT／功率模組 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| IC設計 | MCU | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 被動元件 | MLCC | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 記憶體 | NAND Flash／SSD | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 記憶體 | NOR Flash／利基型記憶體 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 高速互連 | Retimer／Redriver | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| IC設計 | RISC-V | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 晶圓材料 | SiC 晶圓／基板 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 功率半導體 | SiC／GaN 功率元件 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 封裝測試 | 一般封測 | 10 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電子連接 | 一般連接器 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 大型權值 | 大型電子權值 | 27 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 自動化與機器人 | 工業自動化 | 18 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 傳統產業材料 | 化工原料／塑化報價 | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電力與能源 | 太陽能 | 9 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 功率半導體 | 功率 MOSFET | 8 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 功率半導體 | 功率二極體／整流器 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體設備與權值 | 半導體設備零組件 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 傳統產業材料 | 生技醫藥與CDMO (Biotech & CDMO) | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 被動元件 | 石英元件 | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體設備與權值 | 先進封裝設備 | 12 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 通訊與光電 | 光通訊 | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體製造 | 成熟製程 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 通訊與光電 | 低軌衛星 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 建設開發 | 住宅營建 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體材料 | 利基型光電磊晶 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體材料 | 利基型特用化學 (Specialty Chemical Materials) | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 車用電子 | 車用功率半導體 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 車用電子 | 車用連接器 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI運算與伺服器 | 其他 AI伺服器供應鏈 | 63 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI視覺 | 其他 AI視覺 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| IC設計 | 其他 IC設計 | 20 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 大型權值 | 其他大型權值 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體材料 | 其他半導體材料 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體設備與權值 | 其他半導體設備 | 23 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 車用電子 | 其他車用電子 | 33 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 傳統產業材料 | 其他原物料 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電力與能源 | 其他能源 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 軍工國防 | 其他國防 | 9 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 被動元件 | 其他被動元件 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 通訊與光電 | 其他通訊光電 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 熱管理 | 其他熱管理 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 被動元件 | 固態電容 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 通訊與光電 | 矽光子 | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 功率半導體 | 保護元件 | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體設備與權值 | 玻璃基板 | 9 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| PCB供應鏈 | 玻纖布 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 軍工國防 | 軍工船舶 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電力與能源 | 重電 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 熱管理 | 風冷散熱 | 11 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電子連接 | 特用與精密線束 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體製造 | 特殊製程 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 傳統產業材料 | 特殊鋼／高性能合金 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 傳統產業材料 | 紡織 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 軍工國防 | 航太零組件 | 11 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 全球物流與運輸基建 | 航空客貨運 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體製造 | 記憶體製程 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 記憶體 | 記憶體模組／通路 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 高速互連 | 高速介面 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電子連接 | 高速連接器 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 高速互連 | 高速傳輸 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 封裝測試 | 高階測試介面與探針 (Advanced Testing Interfaces) | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 建設開發 | 商辦／都市更新 | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 熱管理 | 液冷散熱 | 16 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 全球物流與運輸基建 | 貨代與物流 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 全球物流與運輸基建 | 貨櫃海運 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 全球物流與運輸基建 | 散裝航運 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 熱管理 | 散熱零組件 | 8 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體製造 | 晶圓代工 | 0 | PENDING_OWNER_REVIEW_NO_CORE_CANDIDATE | NO_FORMAL_CORE_CANDIDATES; FAIL_CLOSED_IF_UNAPPROVED |
| 軍工國防 | 無人機 | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI視覺 | 視覺檢測 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 資安服務 | 雲端資安 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| PCB供應鏈 | 傳統硬板與軟板 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 軍工國防 | 雷達與感測 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 半導體材料 | 電子化學材料 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 車用電子 | 電動車／EV | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 被動元件 | 電感 | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 資安服務 | 端點資安 | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 通訊與光電 | 網通 | 13 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 資安服務 | 網路資安 | 6 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| PCB供應鏈 | 製程耗材與特料 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| PCB供應鏈 | 銅箔基板CCL | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 被動元件 | 鋁電容 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 自動化與機器人 | 機器人系統整合 | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 自動化與機器人 | 機器人零組件 | 8 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI視覺 | 機器視覺 | 1 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 傳統產業材料 | 鋼鐵／不鏽鋼材料 | 5 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電力與能源 | 儲能 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 建設開發 | 營建工程 | 7 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| 電力與能源 | 離岸風電／鋼構 | 2 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI視覺 | 邊緣運算與智慧影像 (Edge AI & Vision) | 3 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |
| AI運算與伺服器 | 顯卡 | 4 | PENDING_OWNER_REVIEW | OWNER_REVIEW_REQUIRED_FOR_ALL_ROWS |

## Topics with no formal CORE candidates

- `d445a914-7c1c-49d1-9cee-2e815388a8cb` 晶圓代工 - no approved Structural Role CORE candidate; any formal projection must fail closed until authority changes.

## Editing and approval handoff

Review the machine-readable JSON/CSV rows. For each candidate, Owner review must set final inclusion and, only for included members, one legal importance value. The reviewed result must receive its own version, effective date, approval reference, source artifact binding, correction/supersession identity, and lineage hash before it can be ingested into `TopicScoreProjection`.

The generated draft is not a formal runtime authority artifact. No Score, Grade, Lifecycle, Topic, Today, Opportunity, Production, or scheduler state was changed by this generation.

## Provenance

- Structural Role source: `config/topic_structural_role_authority/structural-role-authority-20260912.v4.json`
- Structural Role declared artifact hash: `c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc`
- Structural Role file SHA-256: `49af09debaafb064400dcde34b5e31cc1b0c7651ad4d419fda59b23a61a7b901`
- Topic scope source: `config/topic_authority_v1/lifecycle-formal-scope-20260911.v2.json`
- Topic scope file SHA-256: `1fff8c234e96fdc4db9b959ee62dec6256ede3cd32bea305158390fd0554d8e1`
- Draft content hash (before embedded hash field): `b97f97f4a77beea45b7e15ed06ef8936fc3a4769ea0c8ce02895be7ef64260b6`
- Generator: `scripts/generate_d001_owner_review_draft.ps1`
