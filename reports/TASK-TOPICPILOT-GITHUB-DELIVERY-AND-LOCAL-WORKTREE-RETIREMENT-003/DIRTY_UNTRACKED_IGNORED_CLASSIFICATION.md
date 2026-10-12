# Dirty, Untracked, and Ignored Classification

## Protected dirty worktrees

- `frontend-production-deployment-002`: 14 tracked unstaged paths; full untracked enumeration was not completed in the bounded historical readback. Treat as protected.
- `stock-topic-impact-direction-evidence-ui-001`: 9 tracked unstaged paths and 13 untracked paths, including task report deliverables. Preserve.
- `stock-research-bootstrap-v1`: 9 tracked unstaged paths and 4,906 untracked paths, including research source contracts, reports, PDFs, external-research material, temporary PNGs, and a `venv-yfinance` tree. Preserve; do not blanket-copy or clean.

## Ignored/build material

`node_modules`, build output, caches, virtual environments, downloaded PDFs, temporary PNGs, and credentials are not treated as source delivery. They require file-level provenance and Owner disposition before any deletion or archival.

## Safety result

No `git clean`, `reset --hard`, forced Worktree removal, or blanket ignored-artifact deletion was executed.
