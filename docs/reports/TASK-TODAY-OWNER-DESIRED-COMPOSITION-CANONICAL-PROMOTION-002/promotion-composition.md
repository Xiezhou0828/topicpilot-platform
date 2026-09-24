# Promotion composition

```text
PROMOTION_COMPOSITION_METHOD=CLEAN_CHERRY_PICK
CHERRY_PICK_SOURCE=38eed205f058fa86cb8a21f7fccf726d76ebd1db
CHERRY_PICK_RESULT=9559643
CONFLICT_COUNT=0
CONFLICT_FILES=NONE
CONFLICT_RESOLUTION_STATUS=NO_CONFLICT
```

The candidate commit applied cleanly onto `c177b949`. The resulting diff was
then checked against current `main`. The candidate's generated API-client
deletion of the existing `/api/v1/admin/migration` read-only surface was outside
the Today promotion boundary, so that pre-existing client surface was restored
with the explicit bounded preservation commit `3084497`. No backend source,
Alembic file, Track C source, or API implementation was reverted or changed.

The final promotion branch before adding this report contains:

```text
9559643 feat(today): reconcile owner-desired market composition
3084497 chore(today): preserve canonical migration client surface
```

This preserves current canonical Track C behavior, migration lineage, Topic
hierarchy behavior, Stock Explorer behavior, and Favorites behavior while
adding only the validated Today composition and its supporting client types.
