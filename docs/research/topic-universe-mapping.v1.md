# TopicPilot V2 Topic Universe Mapping

**Version:** `topic-universe-mapping.v1`
**Status:** `RESEARCH DATASET / NOT APPROVED`
**Source date:** 2026-08-09

This artifact joins the stock universe to the supplied topic hierarchy and topic-group descriptions. It does not change topic membership, approve leaders, or activate production.

- Stock rows: **539**; rows with stock code: **507**
- Hierarchy rows: **107**; enabled hierarchy topics: **107**
- Topic database rows: **130**
- Mapping rows: **1042**; matched: **1031**; unmapped: **11**
- Topics with stock coverage: **104**

## Mapping rules

1. Only stock rows with a non-empty `股號` are included.
2. `主要題材` becomes `PRIMARY`; `副題材` becomes `SECONDARY`. Comma-separated labels are exploded.
3. Topic names are matched exactly after trimming against `細題材`; no silent synonym or typo correction is applied.
4. Descriptions come from the matching `題材` row in the topic database.

## Topic coverage summary

| Topic | Parent | Stocks | Role | Enabled | Description |
|---|---|---:|---|---|---|
| 12 吋矽晶圓 | 晶圓材料 | 4 | 核心 | Y | available |
| 8 吋矽晶圓 | 晶圓材料 | 4 | 核心 | Y | available |
| ABF載板 | 封裝測試 | 4 | 細分題材 | Y | available |
| ADAS | 車用電子 | 6 | 主流 | Y | available |
| AI PCB | AI運算與伺服器 | 9 | 核心 | Y | available |
| AI伺服器整機／ODM | AI運算與伺服器 | 16 | 核心 | Y | available |
| AI影像辨識 | AI視覺 | 5 | 主流 | Y | available |
| AI電力基建 | 電力與能源 | 14 | 主流 | Y | available |
| ASIC | IC設計 | 7 | 核心 | Y | available |
| BBU | AI運算與伺服器 | 5 | 主流 | Y | available |
| CCL | 高頻電子材料 | 12 | 核心 | Y | available |
| Chiplet | 封裝測試 | 12 | 次主流 | Y | available |
| CoWoS | 封裝測試 | 12 | 主流 | Y | available |
| DRAM／DDR | 記憶體 | 9 | 核心 | Y | available |
| FOPLP | 封裝測試 | 8 | 主流 | Y | available |
| GaN 晶圓／GaN-on-Si | 晶圓材料 | 2 | 次主流 | Y | available |
| IGBT／功率模組 | 功率半導體 | 4 | 核心 | Y | available |
| MCU | IC設計 | 3 | 核心 | Y | available |
| MLCC | 被動元件 | 5 | 核心 | Y | available |
| NAND Flash／SSD | 記憶體 | 8 | 核心 | Y | available |
| NOR Flash／利基型記憶體 | 記憶體 | 4 | 次主流 | Y | available |
| PCB | 高頻電子材料 | 7 | 核心 | Y | available |
| RISC-V | IC設計 | 3 | 主流 | Y | available |
| Retimer／Redriver | 高速互連 | 1 | 主流 | Y | available |
| SiC 晶圓／基板 | 晶圓材料 | 3 | 主流 | Y | available |
| SiC／GaN 功率元件 | 功率半導體 | 5 | 主流 | Y | available |
| 一般封測 | 封裝測試 | 16 | 核心 | Y | available |
| 一般連接器 | 電子連接 | 9 | 核心 | Y | available |
| 低軌衛星 | 通訊與光電 | 10 | 主流 | Y | available |
| 住宅營建 | 建設開發 | 15 | 核心 | Y | available |
| 保護元件 | 功率半導體 | 4 | 補充 | Y | available |
| 儲能 | 電力與能源 | 17 | 主流 | Y | available |
| 先進封裝設備 | 半導體設備與製程 | 19 | 核心 | Y | available |
| 光通訊 | 通訊與光電 | 16 | 核心 | Y | available |
| 其他 AI伺服器供應鏈 | AI運算與伺服器 | 62 | 補充 | Y | available |
| 其他 AI視覺 | AI視覺 | 1 | 補充 | Y | available |
| 其他 IC設計 | IC設計 | 34 | 補充 | Y | available |
| 其他動元件 |  | 1 |  |  | missing |
| 其他半導體設備 | 半導體設備與製程 | 30 | 補充 | Y | available |
| 其他原物料 | 傳統產業材料 | 82 | 補充 | Y | available |
| 其他國防 | 軍工國防 | 12 | 補充 | Y | available |
| 其他大型權值 | 大型權值 | 3 | 補充 | Y | available |
| 其他能源 | 電力與能源 | 5 | 補充 | Y | available |
| 其他被動元件 | 被動元件 | 19 | 補充 | Y | available |
| 其他車用電子 | 車用電子 | 54 | 補充 | Y | available |
| 其他通訊光電 | 通訊與光電 | 5 | 補充 | Y | available |
| 其他連接器 | 電子連接 | 1 | 補充 | Y | available |
| 功率 MOSFET | 功率半導體 | 11 | 核心 | Y | available |
| 功率二極體／整流器 | 功率半導體 | 6 | 主流 | Y | available |
| 功率半導體 |  | 1 |  |  | available |
| 化工原料／塑化報價 | 傳統產業材料 | 15 | 核心 | Y | available |
| 半導體原料 | 半導體材料 | 4 | 核心 | Y | available |
| 半導體設備零組件 | 半導體設備與製程 | 7 | 核心 | Y | available |
| 商辦／都市更新 | 建設開發 | 11 | 主流 | Y | available |
| 固態電容 | 被動元件 | 3 | 主流 | Y | available |
| 大型電子權值 | 大型權值 | 44 | 核心 | Y | available |
| 太陽能 | 電力與能源 | 16 | 核心 | Y | available |
| 工業自動化 | 自動化與機器人 | 26 | 核心 | Y | available |
| 成熟製程 | 半導體製造 | 3 | 核心 | Y | available |
| 散熱零組件 | 熱管理 | 13 | 主流 | Y | available |
| 晶圓代工 | 半導體製造 | 3 | 核心 | Y | available |
| 晶圓材料 |  | 1 |  |  | available |
| 核心 IC設計 |  | 1 |  |  | missing |
| 機器人系統整合 | 自動化與機器人 | 8 | 主流 | Y | available |
| 機器人零組件 | 自動化與機器人 | 11 | 核心 | Y | available |
| 機器視覺 | AI視覺 | 10 | 核心 | Y | available |
| 液冷散熱 | 熱管理 | 11 | 核心 | Y | available |
| 無人機 | 軍工國防 | 7 | 核心 | Y | available |
| 營建工程 | 建設開發 | 6 | 核心 | Y | available |
| 特殊製程 | 半導體製造 | 4 | 主流 | Y | available |
| 特殊鋼／高性能合金 | 傳統產業材料 | 6 | 主流 | Y | available |
| 玻璃基板 | 半導體設備與製程 | 8 | 主流 | Y | available |
| 玻纖布 | 高頻電子材料 | 4 | 主流 | Y | available |
| 石英元件 | 被動元件 | 5 | 次主流 | Y | available |
| 矽光子 | 通訊與光電 | 15 | 主流 | Y | available |
| 端點資安 | 資安服務 | 8 | 主流 | Y | available |
| 紡織 | 傳統產業材料 | 4 | 主流 | Y | available |
| 網路資安 | 資安服務 | 10 | 核心 | Y | available |
| 網通 | 通訊與光電 | 31 | 核心 | Y | available |
| 航太零組件 | 軍工國防 | 17 | 核心 | Y | available |
| 視覺檢測 | AI視覺 | 1 | 核心 | Y | available |
| 記憶體模組／通路 | 記憶體 | 11 | 主流 | Y | available |
| 記憶體製程 | 半導體製造 | 1 | 次主流 | Y | available |
| 車用功率半導體 | 車用電子 | 4 | 主流 | Y | available |
| 車用連接器 | 車用電子 | 8 | 主流 | Y | available |
| 車用電子 |  | 2 |  |  | available |
| 軍工船舶 | 軍工國防 | 2 | 主流 | Y | available |
| 通訊與光電 |  | 1 |  |  | available |
| 重電 | 電力與能源 | 8 | 核心 | Y | available |
| 鋁電容 | 被動元件 | 5 | 主流 | Y | available |
| 鋼鐵／不鏽鋼材料 | 傳統產業材料 | 11 | 核心 | Y | available |
| 開他 AI伺服器供應鏈 |  | 2 |  |  | missing |
| 離岸風電／鋼構 | 電力與能源 | 4 | 次主流 | Y | available |
| 雲端資安 | 資安服務 | 7 | 主流 | Y | available |
| 雷達與感測 | 軍工國防 | 6 | 核心 | Y | available |
| 電動車／EV | 車用電子 | 6 | 核心 | Y | available |
| 電子化學材料 | 半導體材料 | 6 | 核心 | Y | available |
| 電感 | 被動元件 | 7 | 核心 | Y | available |
| 顯卡 | AI運算與伺服器 | 8 | 核心 | Y | available |
| 風冷散熱 | 熱管理 | 9 | 核心 | Y | available |
| 高速介面 | 高速互連 | 4 | 主流 | Y | available |
| 高速傳輸 | 高速互連 | 4 | 核心 | Y | available |
| 高速連接器 | 電子連接 | 6 | 核心 | Y | available |
| 高頻電子材料 |  | 2 |  |  | available |

## Unmapped labels requiring review

- `其他動元件` — 1 relation row(s); absent from the supplied hierarchy.
- `功率半導體` — 1 relation row(s); absent from the supplied hierarchy.
- `晶圓材料` — 1 relation row(s); absent from the supplied hierarchy.
- `核心 IC設計` — 1 relation row(s); absent from the supplied hierarchy.
- `車用電子` — 2 relation row(s); absent from the supplied hierarchy.
- `通訊與光電` — 1 relation row(s); absent from the supplied hierarchy.
- `開他 AI伺服器供應鏈` — 2 relation row(s); absent from the supplied hierarchy.
- `高頻電子材料` — 2 relation row(s); absent from the supplied hierarchy.

## Governance notes

- This is a membership mapping foundation, not an approved Leader Set.
- CORE/PRIMARY basis still requires PM confirmation.
- Rows without stock codes and unmapped labels are classification-debt queues, not silently discarded business truth.

## Source files

A separate Leader Set candidate pool was created at `C:\Users\acer\Desktop\題材領航\topicpilot-platform\fixtures\research\leader_set_candidate_pool.v1.csv`. It contains only supplied `主要題材`/PRIMARY members, all marked `NEEDS_REVIEW`, with no importance weights and no approval claim. This follows the research rule that evidence must precede leader assignment.

- `C:\Users\acer\Downloads\股票分類v5 - 股票總覽 (2).tsv`
- `C:\Users\acer\Downloads\股票分類v5 - 題材階層表 (2).tsv`
- `C:\Users\acer\Downloads\股票分類v5 - 族群資料庫 (2).tsv`
