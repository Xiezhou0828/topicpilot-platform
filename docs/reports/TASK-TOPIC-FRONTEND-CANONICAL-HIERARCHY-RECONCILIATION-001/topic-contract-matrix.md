# Topic contract matrix

| Concern | Canonical authority | Frontend treatment | Parent | Leaf |
| --- | --- | --- | --- | --- |
| Identity | `GET /api/v2/topic-catalog` and `GET /api/v2/topic-catalog/{slug}` | `TopicCatalogNode` supplies `topicId`, `slug`, `name`, `enabled`, and `kind`. | Visible without a daily state row. | Visible even when Leaf state is temporarily unavailable. |
| Hierarchy | Catalog `hierarchy.parents[]` / `hierarchy.children[]` | All group browsing and detail links use explicit edges. `groupName` is display convenience only. | Children are canonical Catalog nodes. | Parents are canonical Catalog nodes; ungrouped Leaf remains explicitly ungrouped. |
| Kind | Catalog `kind: PARENT | LEAF` | `kind` drives list lanes, detail branches, and stock filter options. | Excluded from market/score/lifecycle lanes. | Included in Leaf market lanes. |
| Leaf state | Legacy `/api/v2/topics` compatibility read model | Joined by slug as optional state; it cannot remove Catalog identity. | No state row is expected. | State fields are used when returned; otherwise the UI discloses unavailable/deferred values. |
| Formal snapshot | Catalog `currentFormalSnapshot` | Snapshot availability and reason are preserved; Catalog snapshot values are used only when present. | `NOT_APPLICABLE`. | `AVAILABLE`, `UNAVAILABLE`, or deferred is shown without browser derivation. |
| Members | Catalog `members` plus optional legacy detail constituents | Detail keeps relation order and never browser-ranks members. | `NOT_APPLICABLE`; no fake members. | Uses formal state constituents when present, otherwise Catalog members. |
| Score / Grade | Leaf state or Catalog current snapshot | No score or grade calculation in the browser. | `NOT_APPLICABLE`. | `null`/unavailable stays disclosed. |
| Lifecycle | Legacy formal Leaf state | Lifecycle is optional and guarded at render time. | `NOT_APPLICABLE`. | Backend lifecycle and unavailable states are preserved. |
| Fallback | Configured Catalog API availability | Configured API failure is unavailable; synthetic Preview is not mixed into formal Catalog data. | No synthetic Parent. | No synthetic hierarchy is inferred from labels. |

Generated OpenAPI/client declarations already contain all four Catalog routes and the Catalog schemas. `npm run check` confirmed that `openapi.json`, generated client types, and the web declaration remain synchronized.
