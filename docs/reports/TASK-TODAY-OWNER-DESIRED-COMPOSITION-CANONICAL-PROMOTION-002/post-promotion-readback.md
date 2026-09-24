# Post-promotion canonical readback

The feature promotion was fast-forwarded to remote `main` and read back from
`origin/main` at the following SHA:

```text
REMOTE_MAIN_HEAD_AFTER=7314ecdd2936cbfa4bee5cd1d0eb1fcd5ff56978
```

```text
CANONICAL_TODAY_READBACK_STATUS=PASS
CANONICAL_TRACK_C_SOURCE_PRESERVED=YES
CANONICAL_MIGRATION_GRAPH_STATUS=PASS
CANONICAL_TOPIC_SOURCE_PRESERVED=YES
CANONICAL_STOCK_SOURCE_PRESERVED=YES
CANONICAL_FAVORITES_SOURCE_PRESERVED=YES
```

Readback evidence:

- `apps/web/app/components/v2/TodayMarketPage.tsx` contains `市場概況`,
  `今日市場重點`, `今日主線`, conditional `GradeChip`, and canonical Topic
  links.
- Track C source remains present in `services/api/src/topicpilot_api/`,
  including the relation-weight authority and workbook modules.
- `services/api/alembic/versions/0046_task_stock_maint_relation_weight_authority_001d.py`
  remains present with revision `0046_task_stock_maint_relation_weight_authority_001d`
  and parent `0045_task_m1_formal_score_grade_publication`.
- Topic source remains `TopicListPage.tsx` and `TopicDetailPage.tsx`.
- Stock source remains `StockExplorerPage.tsx` and Favorites source remains
  `FavoritesWorkspacePage.tsx`.

The final feature promotion changed no file under `services/api` relative to
the pre-promotion canonical `main`. No migration was applied and no database or
Production runtime was touched.
