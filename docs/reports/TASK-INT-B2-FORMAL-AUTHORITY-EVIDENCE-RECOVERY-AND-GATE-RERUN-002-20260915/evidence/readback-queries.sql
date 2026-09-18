-- TASK-TOPIC-B2-107-25-FORMAL-DB-READBACK-001
-- Production-only SELECT evidence. No DDL/DML/migration/publication statements.

SELECT version_num FROM public.alembic_version LIMIT 1;

WITH current_topics AS (
  SELECT t.* FROM topicpilot.topics t
  WHERE t.status = 'ENABLED'
    AND t.valid_from <= DATE '2026-09-15'
    AND (t.valid_to IS NULL OR t.valid_to >= DATE '2026-09-15')
), current_edges AS (
  SELECT DISTINCT h.parent_topic_id, h.child_topic_id
  FROM topicpilot.topic_hierarchy h
  WHERE h.valid_from <= DATE '2026-09-15'
    AND (h.valid_to IS NULL OR h.valid_to >= DATE '2026-09-15')
    AND EXISTS (SELECT 1 FROM current_topics p WHERE p.id = h.parent_topic_id)
    AND EXISTS (SELECT 1 FROM current_topics c WHERE c.id = h.child_topic_id)
)
SELECT
  (SELECT count(*) FROM current_topics) AS active_topics,
  (SELECT count(DISTINCT parent_topic_id) FROM current_edges) AS parent_topics,
  (SELECT count(DISTINCT child_topic_id) FROM current_edges) AS leaf_topics,
  (SELECT count(*) FROM current_edges) AS hierarchy_edges;

SELECT
  count(*) AS canonical_artifact_role_rows,
  count(*) FILTER (WHERE structural_role IS NOT NULL) AS structural_role_nonnull,
  count(*) FILTER (WHERE approval_state = 'APPROVED') AS approved,
  count(*) FILTER (WHERE authority_version = 'structural-role-authority-20260912.v4') AS authority_version_exact,
  count(*) FILTER (WHERE source_artifact_hash = 'c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc') AS source_artifact_exact
FROM topicpilot.instrument_topic_relations;

SELECT
  r.relation_type,
  r.structural_role,
  r.relation_version,
  r.approval_state,
  count(*) AS row_count
FROM topicpilot.instrument_topic_relations r
WHERE r.source_artifact_hash = 'c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc'
GROUP BY 1, 2, 3, 4
ORDER BY 1, 2, 3, 4;

SELECT
  activation_version,
  artifact_sha256,
  source_master_sha256,
  source_revision,
  target_environment,
  target_database,
  status,
  active_parent_count,
  active_leaf_count,
  lifecycle_scope_count,
  readback_sha256,
  effective_from,
  approval_reference
FROM topicpilot.topic_authority_activations
ORDER BY effective_from DESC
LIMIT 10;

-- md5 is used because pgcrypto/digest is not installed in this database.
-- Topic and hierarchy SHA-256 values are also recorded from the official API.
WITH current_topics AS (
  SELECT t.* FROM topicpilot.topics t
  WHERE t.status = 'ENABLED'
    AND t.valid_from <= DATE '2026-09-15'
    AND (t.valid_to IS NULL OR t.valid_to >= DATE '2026-09-15')
), current_edges AS (
  SELECT DISTINCT h.parent_topic_id, h.child_topic_id
  FROM topicpilot.topic_hierarchy h
  WHERE h.valid_from <= DATE '2026-09-15'
    AND (h.valid_to IS NULL OR h.valid_to >= DATE '2026-09-15')
), topic_lines AS (
  SELECT concat_ws('|', t.id::text,
    CASE WHEN EXISTS (SELECT 1 FROM current_edges e WHERE e.parent_topic_id = t.id)
      THEN 'PARENT' ELSE 'LEAF' END,
    t.slug, t.name, t.status) AS line
  FROM current_topics t
), edge_lines AS (
  SELECT concat_ws('|', parent_topic_id::text, child_topic_id::text) AS line
  FROM current_edges
), role_lines AS (
  SELECT concat_ws('|', m.code, i.instrument_code, r.topic_id::text,
    r.relation_type, r.structural_role, r.approval_state) AS line
  FROM topicpilot.instrument_topic_relations r
  JOIN topicpilot.instruments i ON i.id = r.instrument_id
  JOIN topicpilot.markets m ON m.id = i.market_id
  WHERE r.source_artifact_hash = 'c35c15911c355766dbaa53e76629ae17c84f8d1bbc98e2053b7e87592c0274bc'
)
SELECT 'topic_identity' AS dataset, count(*) AS row_count,
  md5(string_agg(line, E'\n' ORDER BY line)) AS md5 FROM topic_lines
UNION ALL
SELECT 'hierarchy_edges', count(*),
  md5(string_agg(line, E'\n' ORDER BY line)) FROM edge_lines
UNION ALL
SELECT 'role_content_by_canonical_artifact', count(*),
  md5(string_agg(line, E'\n' ORDER BY line)) FROM role_lines
ORDER BY dataset;
