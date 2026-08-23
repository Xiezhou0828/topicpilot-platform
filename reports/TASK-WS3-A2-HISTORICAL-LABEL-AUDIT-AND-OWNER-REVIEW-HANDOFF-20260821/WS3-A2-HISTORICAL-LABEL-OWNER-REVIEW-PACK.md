# WS3 A2 Historical Label Owner Review Pack

TASK_ID: `TASK-WS3-A2-HISTORICAL-LABEL-AUDIT-AND-OWNER-REVIEW-HANDOFF-20260821`
TASK_STATUS: `OWNER_REVIEW_REQUIRED`
MODE: `READ-ONLY RESEARCH AUDIT / OWNER REVIEW HANDOFF`

## NEXT OWNER REVIEW ORDER

1. 6727 — 2025-08-04
2. 5321 — 2026-05-18
3. 5386 — 2026-02-02
4. 6861 — 2026-04-21
5. 2434 — 2026-07-01
6. 2483 — 2025-08-08
7. 1563 — 2025-12-22
8. 2312 — 2026-01-12
9. 2243 — 2026-03-25
10. 4576 — 2026-01-14
11. 2414 — 2026-04-16
12. 6654 — 2025-01-09
13. 6416 — 2026-05-05
14. 1476 — 2025-08-14
15. 6643 — 2025-02-13
16. 8150 — 2026-04-15
17. 3630 — 2024-12-19
18. 2472 — 2025-10-21
19. 2467 — 2025-12-08
20. 3443 — 2025-06-25
21. 6204 — 2025-10-20
22. 8261 — 2025-07-18
23. 3441 — 2024-12-25
24. 6642 — 2026-02-23
25. 3556 — 2025-08-29
26. 2327 — 2025-08-05
27. 8277 — 2025-11-13
28. 3055 — 2026-07-15
29. 3675 — 2026-07-06
30. 6668 — 2025-03-28

## Scope and interpretation boundary

This pack audits 30 events already present in the canonical historical A2 expanded event panel: 15 `REVIEW_SUCCESS_PROXY` cases and 15 `REVIEW_FAILURE_PROXY` cases. The source artifacts do not contain an event-level binary historical success/failure label. The proxy split therefore uses the existing A2 artifact win-rate convention at T+10 (`forward_return > 0` is the positive side; non-positive is the negative side) only to construct a deterministic review sample. It is not a strategy acceptance rule and does not relabel the source A2 population.

Setup validity and outcome validity are intentionally independent Owner fields. No Owner fields below are prepopulated.

## Historical A2 qualification reconstruction

The frozen formation rule is preserved exactly: `L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T)`. For each case, the pack records the recoverable reference value, reference policy, reference maturity, Close/MA60 relation, Close/reference relation, gap state, and formation-match field. Missing source fields remain `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.

Current MA60 eligibility is shown separately from the historical label. It is a snapshot, not a retroactive semantic rewrite.

## PIT and outcome availability

The existing A2 panel provides D0 Close, MA60, distance from MA60, volume, reference, and reference metadata. It does not provide the requested D-20/D-10/D-5/D-3/D-1 feature snapshots for these cases; those fields are explicitly left unavailable. T+1/T+3/T+5/T+10 forward return, MFE, and MAE are copied from the existing observable outcome columns without synthetic fill.

## Source and reproducibility

- Source dataset SHA256: `e803733e796d8f4d8cf00575cd4045f28c9364572fc61b31ef490e8a65ff47a4`
- Source dataset window: `2024-08-13 → 2026-08-13`
- Historical A2 event count: `5277`
- Source panel SHA256 from canonical reproducibility manifest: `97b131479b90ce64a821f72a6c6cceb58d102aeb49c64eac60ba19dfca71bc52`
- Canonical protocol source head: `3402adfa9129ca2a6cfad163835b90b54a6d9f3d`
- Audit generator SHA: `8ae27521622e11bb01f7f7e52e1ed8f98d95c124`
- Large panel scans: `1` (the event panel was read once; all outputs were derived from the resulting manifest)
- Parallel A structural eligibility task consulted: `NO`

## Cases

### A2-01 — 6727 — 2025-08-04

- Ticker: 6727
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-08-04
- Historical bucket: SUCCESS_STRONG
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=81.4; ma60=65.64333333333333; close_gt_ma60=PASS; reference=81.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-01-16; reference_age_sessions=130; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=81.4; MA60=65.64333333333333; distance_from_MA60=0.24003453003605357; volume=300000.0; reference=81.0; reference_age_sessions=130; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=81.4; MA60=65.64333333333333; distance_from_MA60=0.24003453003605357; volume=300000.0; reference=81.0; reference_age_sessions=130; gap_up=False
- Forward outcome: T+1=0.09950859950859936; T+3=0.32678132678132665; T+5=0.597051597051597; T+10=1.2604422604422605; MFE T+5=0.597051597051597; MAE T+5=-0.0012285012285013774; MFE T+10=1.2727272727272725; MAE T+10=-0.0012285012285013774
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: highest available T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-02 — 5321 — 2026-05-18

- Ticker: 5321
- Name: 美而快
- Anchor: 2026-05-18
- Historical bucket: SUCCESS_STRONG
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=26.65; ma60=24.455; close_gt_ma60=PASS; reference=25.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-03-06; reference_age_sessions=48; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=26.65; MA60=24.455; distance_from_MA60=0.08975669597219382; volume=405000.0; reference=25.0; reference_age_sessions=48; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=26.65; MA60=24.455; distance_from_MA60=0.08975669597219382; volume=405000.0; reference=25.0; reference_age_sessions=48; gap_up=False
- Forward outcome: T+1=0.09943714821763616; T+3=0.3283302063789868; T+5=0.604127579737336; T+10=1.1538461538461537; MFE T+5=0.604127579737336; MAE T+5=0.018761726078799335; MFE T+10=1.1538461538461537; MAE T+10=0.018761726078799335
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: highest available T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-03 — 5386 — 2026-02-02

- Ticker: 5386
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-02-02
- Historical bucket: SUCCESS_STRONG
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=104.0; ma60=78.67166666666667; close_gt_ma60=PASS; reference=95.3; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-01-05; reference_age_sessions=20; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=104.0; MA60=78.67166666666667; distance_from_MA60=0.32194987606719905; volume=5050000.0; reference=95.3; reference_age_sessions=20; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=104.0; MA60=78.67166666666667; distance_from_MA60=0.32194987606719905; volume=5050000.0; reference=95.3; reference_age_sessions=20; gap_up=True
- Forward outcome: T+1=0.09615384615384626; T+3=0.07211538461538458; T+5=0.29326923076923084; T+10=1.0336538461538463; MFE T+5=0.29326923076923084; MAE T+5=0.0; MFE T+10=1.0336538461538463; MAE T+10=0.0
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: highest available T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-04 — 6861 — 2026-04-21

- Ticker: 6861
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-04-21
- Historical bucket: SUCCESS_STRONG
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=195.0; ma60=116.65166666666667; close_gt_ma60=PASS; reference=178.5; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-03-20; reference_age_sessions=20; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=195.0; MA60=116.65166666666667; distance_from_MA60=0.6716434970210454; volume=7104348.0; reference=178.5; reference_age_sessions=20; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=195.0; MA60=116.65166666666667; distance_from_MA60=0.6716434970210454; volume=7104348.0; reference=178.5; reference_age_sessions=20; gap_up=True
- Forward outcome: T+1=0.10000000000000009; T+3=0.32820512820512815; T+5=0.3999999999999999; T+10=0.9282051282051282; MFE T+5=0.49743589743589745; MAE T+5=0.10000000000000009; MFE T+10=1.2307692307692308; MAE T+10=0.10000000000000009
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: highest available T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-05 — 2434 — 2026-07-01

- Ticker: 2434
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-07-01
- Historical bucket: SUCCESS_STRONG
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=47.75; ma60=33.49; close_gt_ma60=PASS; reference=46.95; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-06-23; reference_age_sessions=6; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=47.75; MA60=33.49; distance_from_MA60=0.42579874589429667; volume=1263581.0; reference=46.95; reference_age_sessions=6; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=47.75; MA60=33.49; distance_from_MA60=0.42579874589429667; volume=1263581.0; reference=46.95; reference_age_sessions=6; gap_up=False
- Forward outcome: T+1=0.09947643979057585; T+3=0.13717277486910984; T+5=0.18324607329842935; T+10=0.9015706806282722; MFE T+5=0.2251308900523561; MAE T+5=0.008376963350785305; MFE T+10=0.9015706806282722; MAE T+10=0.008376963350785305
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: highest available T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-06 — 2483 — 2025-08-08

- Ticker: 2483
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-08-08
- Historical bucket: SUCCESS_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=18.35; ma60=17.788333333333334; close_gt_ma60=PASS; reference=18.2; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-05-06; reference_age_sessions=67; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=18.35; MA60=17.788333333333334; distance_from_MA60=0.031575002342359326; volume=19141.0; reference=18.2; reference_age_sessions=67; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=18.35; MA60=17.788333333333334; distance_from_MA60=0.031575002342359326; volume=19141.0; reference=18.2; reference_age_sessions=67; gap_up=True
- Forward outcome: T+1=0.0735694822888282; T+3=0.0735694822888282; T+5=0.08991825613079008; T+10=0.08174386920980936; MFE T+5=0.10081743869209792; MAE T+5=0.04087193460490468; MFE T+10=0.12534059945504072; MAE T+10=0.04087193460490468
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: closest to the positive-population median T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-07 — 1563 — 2025-12-22

- Ticker: 1563
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-12-22
- Historical bucket: SUCCESS_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=44.65; ma60=44.23083333333334; close_gt_ma60=PASS; reference=42.95; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-12-01; reference_age_sessions=15; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=44.65; MA60=44.23083333333334; distance_from_MA60=0.009476797859713226; volume=1474661.0; reference=42.95; reference_age_sessions=15; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=44.65; MA60=44.23083333333334; distance_from_MA60=0.009476797859713226; volume=1474661.0; reference=42.95; reference_age_sessions=15; gap_up=False
- Forward outcome: T+1=0.025755879059350395; T+3=0.06830907054871238; T+5=0.08734602463605823; T+10=0.08174692049272103; MFE T+5=0.0963045912653977; MAE T+5=-0.013437849944008984; MFE T+10=0.1007838745800671; MAE T+10=-0.013437849944008984
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: closest to the positive-population median T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-08 — 2312 — 2026-01-12

- Ticker: 2312
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-01-12
- Historical bucket: SUCCESS_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=25.05; ma60=22.625; close_gt_ma60=PASS; reference=24.6; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-08-13; reference_age_sessions=345; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=25.05; MA60=22.625; distance_from_MA60=0.10718232044198905; volume=124090953.0; reference=24.6; reference_age_sessions=345; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=25.05; MA60=22.625; distance_from_MA60=0.10718232044198905; volume=124090953.0; reference=24.6; reference_age_sessions=345; gap_up=False
- Forward outcome: T+1=0.09980039920159678; T+3=0.3293413173652693; T+5=0.4131736526946106; T+10=0.08183632734530932; MFE T+5=0.4750499001996009; MAE T+5=0.03992015968063867; MFE T+10=0.4750499001996009; MAE T+10=0.03992015968063867
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: closest to the positive-population median T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-09 — 2243 — 2026-03-25

- Ticker: 2243
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-03-25
- Historical bucket: SUCCESS_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=20.75; ma60=12.8275; close_gt_ma60=PASS; reference=20.7; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-03-18; reference_age_sessions=5; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=20.75; MA60=12.8275; distance_from_MA60=0.6176183979731047; volume=1189336.0; reference=20.7; reference_age_sessions=5; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=20.75; MA60=12.8275; distance_from_MA60=0.6176183979731047; volume=1189336.0; reference=20.7; reference_age_sessions=5; gap_up=False
- Forward outcome: T+1=-0.004819277108433773; T+3=0.10361445783132517; T+5=0.06265060240963849; T+10=0.08192771084337336; MFE T+5=0.10361445783132517; MAE T+5=-0.03614457831325302; MFE T+10=0.18554216867469897; MAE T+10=-0.10602409638554211
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: closest to the positive-population median T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-10 — 4576 — 2026-01-14

- Ticker: 4576
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-01-14
- Historical bucket: SUCCESS_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=116.5; ma60=107.34; close_gt_ma60=PASS; reference=112.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-11-13; reference_age_sessions=42; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=116.5; MA60=107.34; distance_from_MA60=0.08533631451462642; volume=1901619.0; reference=112.0; reference_age_sessions=42; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=116.5; MA60=107.34; distance_from_MA60=0.08533631451462642; volume=1901619.0; reference=112.0; reference_age_sessions=42; gap_up=False
- Forward outcome: T+1=0.0429184549356223; T+3=0.06866952789699576; T+5=0.06008583690987135; T+10=0.0815450643776825; MFE T+5=0.10729613733905574; MAE T+5=-0.030042918454935674; MFE T+10=0.10729613733905574; MAE T+10=-0.030042918454935674
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: closest to the positive-population median T+10 forward return; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-11 — 2414 — 2026-04-16

- Ticker: 2414
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-04-16
- Historical bucket: SUCCESS_BORDERLINE
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=45.65; ma60=42.310833333333335; close_gt_ma60=PASS; reference=45.15; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-09-03; reference_age_sessions=145; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=45.65; MA60=42.310833333333335; distance_from_MA60=0.07891989837118141; volume=382046.0; reference=45.15; reference_age_sessions=145; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=45.65; MA60=42.310833333333335; distance_from_MA60=0.07891989837118141; volume=382046.0; reference=45.15; reference_age_sessions=145; gap_up=True
- Forward outcome: T+1=-0.00766703176341732; T+3=-0.009857612267250682; T+5=0.00766703176341732; T+10=0.0010952902519167917; MFE T+5=0.020810514786418377; MAE T+5=-0.026286966046002114; MFE T+10=0.020810514786418377; MAE T+10=-0.026286966046002114
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: lowest positive T+10 forward returns; borderline by existing win-rate convention.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-12 — 6654 — 2025-01-09

- Ticker: 6654
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-01-09
- Historical bucket: SUCCESS_BORDERLINE
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=44.95; ma60=44.28666666666667; close_gt_ma60=PASS; reference=44.8; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-09-18; reference_age_sessions=69; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=44.95; MA60=44.28666666666667; distance_from_MA60=0.014978172512419174; volume=18000.0; reference=44.8; reference_age_sessions=69; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=44.95; MA60=44.28666666666667; distance_from_MA60=0.014978172512419174; volume=18000.0; reference=44.8; reference_age_sessions=69; gap_up=False
- Forward outcome: T+1=0.0022246941045604984; T+3=-0.032258064516129115; T+5=-0.03893214682981094; T+10=0.0011123470522802492; MFE T+5=0.010011123470522687; MAE T+5=-0.05005561735261399; MFE T+10=0.023359288097886566; MAE T+10=-0.05005561735261399
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: lowest positive T+10 forward returns; borderline by existing win-rate convention.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-13 — 6416 — 2026-05-05

- Ticker: 6416
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-05-05
- Historical bucket: SUCCESS_BORDERLINE
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=87.3; ma60=81.52666666666667; close_gt_ma60=PASS; reference=85.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-10-21; reference_age_sessions=126; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=87.3; MA60=81.52666666666667; distance_from_MA60=0.07081527516558994; volume=672664.0; reference=85.0; reference_age_sessions=126; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=87.3; MA60=81.52666666666667; distance_from_MA60=0.07081527516558994; volume=672664.0; reference=85.0; reference_age_sessions=126; gap_up=False
- Forward outcome: T+1=-0.019473081328751474; T+3=-0.032073310423825885; T+5=-0.038946162657502725; T+10=0.001145475372279492; MFE T+5=0.008018327605956443; MAE T+5=-0.050400916380297756; MFE T+10=0.07101947308132872; MAE T+10=-0.050400916380297756
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: lowest positive T+10 forward returns; borderline by existing win-rate convention.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-14 — 1476 — 2025-08-14

- Ticker: 1476
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-08-14
- Historical bucket: SUCCESS_BORDERLINE
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=407.0; ma60=405.75; close_gt_ma60=PASS; reference=403.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-07-11; reference_age_sessions=24; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=407.0; MA60=405.75; distance_from_MA60=0.0030807147258162804; volume=2541845.0; reference=403.0; reference_age_sessions=24; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=407.0; MA60=405.75; distance_from_MA60=0.0030807147258162804; volume=2541845.0; reference=403.0; reference_age_sessions=24; gap_up=False
- Forward outcome: T+1=0.024570024570024662; T+3=-0.002457002457002422; T+5=-0.013513513513513487; T+10=0.0012285012285011554; MFE T+5=0.05651105651105648; MAE T+5=-0.03685503685503688; MFE T+10=0.05651105651105648; MAE T+10=-0.03685503685503688
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: lowest positive T+10 forward returns; borderline by existing win-rate convention.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-15 — 6643 — 2025-02-13

- Ticker: 6643
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-02-13
- Historical bucket: SUCCESS_BORDERLINE
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_SUCCESS_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=762.0; ma60=709.35; close_gt_ma60=PASS; reference=742.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-01-07; reference_age_sessions=20; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=762.0; MA60=709.35; distance_from_MA60=0.07422288010150124; volume=2822000.0; reference=742.0; reference_age_sessions=20; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=762.0; MA60=709.35; distance_from_MA60=0.07422288010150124; volume=2822000.0; reference=742.0; reference_age_sessions=20; gap_up=False
- Forward outcome: T+1=0.027559055118110187; T+3=0.03937007874015741; T+5=0.06561679790026242; T+10=0.001312335958005173; MFE T+5=0.09448818897637801; MAE T+5=-0.013123359580052507; MFE T+10=0.09448818897637801; MAE T+10=-0.034120734908136496
- Machine historical interpretation: REVIEW_SUCCESS_PROXY; Outcome-only proxy: lowest positive T+10 forward returns; borderline by existing win-rate convention.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-16 — 8150 — 2026-04-15

- Ticker: 8150
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-04-15
- Historical bucket: FAILURE_STRONG_SETUP
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=67.0; ma60=60.71666666666667; close_gt_ma60=PASS; reference=66.1; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-03-18; reference_age_sessions=18; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=67.0; MA60=60.71666666666667; distance_from_MA60=0.10348613779851767; volume=39697424.0; reference=66.1; reference_age_sessions=18; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=67.0; MA60=60.71666666666667; distance_from_MA60=0.10348613779851767; volume=39697424.0; reference=66.1; reference_age_sessions=18; gap_up=False
- Forward outcome: T+1=0.10000000000000009; T+3=0.005970149253731405; T+5=0.19104477611940296; T+10=0.0; MFE T+5=0.20447761194029845; MAE T+5=-0.005970149253731405; MFE T+10=0.20447761194029845; MAE T+10=-0.04179104477611939
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: highest non-positive T+10 forward returns; setup quality is not inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-17 — 3630 — 2024-12-19

- Ticker: 3630
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2024-12-19
- Historical bucket: FAILURE_STRONG_SETUP
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=27.5; ma60=26.705833333333334; close_gt_ma60=PASS; reference=27.35; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-12-02; reference_age_sessions=12; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=27.5; MA60=26.705833333333334; distance_from_MA60=0.02973757293974466; volume=1993000.0; reference=27.35; reference_age_sessions=12; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=27.5; MA60=26.705833333333334; distance_from_MA60=0.02973757293974466; volume=1993000.0; reference=27.35; reference_age_sessions=12; gap_up=False
- Forward outcome: T+1=-0.016363636363636358; T+3=-0.07999999999999996; T+5=0.11090909090909085; T+10=0.0; MFE T+5=0.11090909090909085; MAE T+5=-0.08727272727272717; MFE T+10=0.11818181818181817; MAE T+10=-0.08727272727272717
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: highest non-positive T+10 forward returns; setup quality is not inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-18 — 2472 — 2025-10-21

- Ticker: 2472
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-10-21
- Historical bucket: FAILURE_STRONG_SETUP
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=103.0; ma60=84.61; close_gt_ma60=PASS; reference=95.5; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-09-22; reference_age_sessions=18; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=103.0; MA60=84.61; distance_from_MA60=0.21735019501240993; volume=29808678.0; reference=95.5; reference_age_sessions=18; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=103.0; MA60=84.61; distance_from_MA60=0.21735019501240993; volume=29808678.0; reference=95.5; reference_age_sessions=18; gap_up=True
- Forward outcome: T+1=0.043689320388349495; T+3=0.11165048543689315; T+5=0.10194174757281549; T+10=0.0; MFE T+5=0.14563106796116498; MAE T+5=-0.014563106796116498; MFE T+10=0.14563106796116498; MAE T+10=-0.024271844660194164
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: highest non-positive T+10 forward returns; setup quality is not inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-19 — 2467 — 2025-12-08

- Ticker: 2467
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-12-08
- Historical bucket: FAILURE_STRONG_SETUP
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=226.5; ma60=187.05833333333334; close_gt_ma60=PASS; reference=208.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-11-28; reference_age_sessions=6; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=226.5; MA60=187.05833333333334; distance_from_MA60=0.21085222969661865; volume=8655725.0; reference=208.0; reference_age_sessions=6; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=226.5; MA60=187.05833333333334; distance_from_MA60=0.21085222969661865; volume=8655725.0; reference=208.0; reference_age_sessions=6; gap_up=True
- Forward outcome: T+1=-0.0066225165562914245; T+3=0.07284768211920523; T+5=0.08388520971302427; T+10=0.0; MFE T+5=0.11037527593818974; MAE T+5=-0.04194260485651213; MFE T+10=0.11037527593818974; MAE T+10=-0.04194260485651213
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: highest non-positive T+10 forward returns; setup quality is not inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-20 — 3443 — 2025-06-25

- Ticker: 3443
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-06-25
- Historical bucket: FAILURE_STRONG_SETUP
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=1225.0; ma60=1077.6; close_gt_ma60=PASS; reference=1195.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-11-01; reference_age_sessions=155; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=1225.0; MA60=1077.6; distance_from_MA60=0.13678544914625101; volume=4764145.0; reference=1195.0; reference_age_sessions=155; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=1225.0; MA60=1077.6; distance_from_MA60=0.13678544914625101; volume=4764145.0; reference=1195.0; reference_age_sessions=155; gap_up=False
- Forward outcome: T+1=-0.008163265306122436; T+3=0.06530612244897949; T+5=0.08163265306122458; T+10=0.0; MFE T+5=0.09795918367346945; MAE T+5=-0.020408163265306145; MFE T+10=0.09795918367346945; MAE T+10=-0.020408163265306145
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: highest non-positive T+10 forward returns; setup quality is not inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-21 — 6204 — 2025-10-20

- Ticker: 6204
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-10-20
- Historical bucket: FAILURE_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=80.1; ma60=63.306666666666665; close_gt_ma60=PASS; reference=75.5; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-09-23; reference_age_sessions=16; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=80.1; MA60=63.306666666666665; distance_from_MA60=0.26526958719460825; volume=1728000.0; reference=75.5; reference_age_sessions=16; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=80.1; MA60=63.306666666666665; distance_from_MA60=0.26526958719460825; volume=1728000.0; reference=75.5; reference_age_sessions=16; gap_up=True
- Forward outcome: T+1=-0.043695380774032455; T+3=-0.09737827715355807; T+5=-0.011235955056179692; T+10=-0.05493133583021215; MFE T+5=0.03245942571785276; MAE T+5=-0.09737827715355807; MFE T+10=0.08739076154806491; MAE T+10=-0.09737827715355807
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: closest to the non-positive-population median T+10 forward return.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-22 — 8261 — 2025-07-18

- Ticker: 8261
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-07-18
- Historical bucket: FAILURE_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=85.5; ma60=79.68833333333333; close_gt_ma60=PASS; reference=84.6; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-10-07; reference_age_sessions=189; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=85.5; MA60=79.68833333333333; distance_from_MA60=0.07292995628803878; volume=2104294.0; reference=84.6; reference_age_sessions=189; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=85.5; MA60=79.68833333333333; distance_from_MA60=0.07292995628803878; volume=2104294.0; reference=84.6; reference_age_sessions=189; gap_up=False
- Forward outcome: T+1=0.03040935672514622; T+3=0.021052631578947434; T+5=0.023391812865497075; T+10=-0.054970760233918115; MFE T+5=0.05263157894736836; MAE T+5=0.0011695906432747094; MFE T+10=0.05263157894736836; MAE T+10=-0.07485380116959073
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: closest to the non-positive-population median T+10 forward return.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-23 — 3441 — 2024-12-25

- Ticker: 3441
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2024-12-25
- Historical bucket: FAILURE_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=38.2; ma60=37.60916666666667; close_gt_ma60=PASS; reference=37.5; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-12-18; reference_age_sessions=5; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=38.2; MA60=37.60916666666667; distance_from_MA60=0.015709822516673855; volume=1408000.0; reference=37.5; reference_age_sessions=5; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=38.2; MA60=37.60916666666667; distance_from_MA60=0.015709822516673855; volume=1408000.0; reference=37.5; reference_age_sessions=5; gap_up=False
- Forward outcome: T+1=0.09685863874345535; T+3=0.027486910994764413; T+5=0.002617801047120283; T+10=-0.054973821989528826; MFE T+5=0.09947643979057585; MAE T+5=-0.002617801047120505; MFE T+10=0.09947643979057585; MAE T+10=-0.05628272251308919
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: closest to the non-positive-population median T+10 forward return.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-24 — 6642 — 2026-02-23

- Ticker: 6642
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-02-23
- Historical bucket: FAILURE_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=58.3; ma60=53.45; close_gt_ma60=PASS; reference=57.7; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-10-23; reference_age_sessions=77; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=58.3; MA60=53.45; distance_from_MA60=0.09073900841908311; volume=263000.0; reference=57.7; reference_age_sessions=77; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=58.3; MA60=53.45; distance_from_MA60=0.09073900841908311; volume=263000.0; reference=57.7; reference_age_sessions=77; gap_up=False
- Forward outcome: T+1=0.0; T+3=-0.013722126929674006; T+5=-0.01715265866209259; T+10=-0.054888507718696355; MFE T+5=0.005145797598627766; MAE T+5=-0.02572898799313894; MFE T+10=0.005145797598627766; MAE T+10=-0.07375643224699824
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: closest to the non-positive-population median T+10 forward return.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-25 — 3556 — 2025-08-29

- Ticker: 3556
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-08-29
- Historical bucket: FAILURE_TYPICAL
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=40.0; ma60=37.09916666666667; close_gt_ma60=PASS; reference=37.85; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-08-20; reference_age_sessions=7; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=40.0; MA60=37.09916666666667; distance_from_MA60=0.0781913340371525; volume=444000.0; reference=37.85; reference_age_sessions=7; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=40.0; MA60=37.09916666666667; distance_from_MA60=0.0781913340371525; volume=444000.0; reference=37.85; reference_age_sessions=7; gap_up=False
- Forward outcome: T+1=-0.02750000000000008; T+3=-0.03125; T+5=-0.03125; T+10=-0.05500000000000005; MFE T+5=0.006250000000000089; MAE T+5=-0.06750000000000012; MFE T+10=0.006250000000000089; MAE T+10=-0.07250000000000001
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: closest to the non-positive-population median T+10 forward return.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-26 — 2327 — 2025-08-05

- Ticker: 2327
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-08-05
- Historical bucket: FAILURE_CLEAR
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=550.0; ma60=495.0833333333333; close_gt_ma60=PASS; reference=545.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2024-11-05; reference_age_sessions=182; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=550.0; MA60=495.0833333333333; distance_from_MA60=0.11092408685406507; volume=6201081.0; reference=545.0; reference_age_sessions=182; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=550.0; MA60=495.0833333333333; distance_from_MA60=0.11092408685406507; volume=6201081.0; reference=545.0; reference_age_sessions=182; gap_up=False
- Forward outcome: T+1=-0.016363636363636358; T+3=-0.009090909090909038; T+5=-0.014545454545454528; T+10=-0.750909090909091; MFE T+5=0.0018181818181817189; MAE T+5=-0.032727272727272716; MFE T+10=0.0018181818181817189; MAE T+10=-0.7527272727272727
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: lowest available T+10 forward returns; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-27 — 8277 — 2025-11-13

- Ticker: 8277
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-11-13
- Historical bucket: FAILURE_CLEAR
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=16.45; ma60=12.872; close_gt_ma60=PASS; reference=16.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-10-09; reference_age_sessions=23; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=16.45; MA60=12.872; distance_from_MA60=0.2779676817899317; volume=7438000.0; reference=16.0; reference_age_sessions=23; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=16.45; MA60=12.872; distance_from_MA60=0.2779676817899317; volume=7438000.0; reference=16.0; reference_age_sessions=23; gap_up=False
- Forward outcome: T+1=-0.06079027355623101; T+3=-0.1671732522796353; T+5=-0.3221884498480243; T+10=-0.5075987841945289; MFE T+5=-0.009118541033434568; MAE T+5=-0.3221884498480243; MFE T+10=-0.009118541033434568; MAE T+10=-0.5349544072948328
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: lowest available T+10 forward returns; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-28 — 3055 — 2026-07-15

- Ticker: 3055
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-07-15
- Historical bucket: FAILURE_CLEAR
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=193.0; ma60=106.73333333333333; close_gt_ma60=PASS; reference=176.5; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-07-07; reference_age_sessions=5; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=193.0; MA60=106.73333333333333; distance_from_MA60=0.8082448469706434; volume=1264219.0; reference=176.5; reference_age_sessions=5; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=193.0; MA60=106.73333333333333; distance_from_MA60=0.8082448469706434; volume=1264219.0; reference=176.5; reference_age_sessions=5; gap_up=False
- Forward outcome: T+1=-0.06735751295336789; T+3=-0.16321243523316065; T+5=-0.1424870466321243; T+10=-0.4637305699481865; MFE T+5=0.041450777202072464; MAE T+5=-0.2227979274611399; MFE T+10=0.041450777202072464; MAE T+10=-0.4637305699481865
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: lowest available T+10 forward returns; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-29 — 3675 — 2026-07-06

- Ticker: 3675
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2026-07-06
- Historical bucket: FAILURE_CLEAR
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=450.0; ma60=300.18333333333334; close_gt_ma60=PASS; reference=445.5; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2026-06-23; reference_age_sessions=9; reference_maturity=PASS; gap_up=True; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=450.0; MA60=300.18333333333334; distance_from_MA60=0.4990838931763921; volume=725000.0; reference=445.5; reference_age_sessions=9; gap_up=True
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=450.0; MA60=300.18333333333334; distance_from_MA60=0.4990838931763921; volume=725000.0; reference=445.5; reference_age_sessions=9; gap_up=True
- Forward outcome: T+1=-0.09999999999999998; T+3=-0.12; T+5=-0.26222222222222225; T+10=-0.40555555555555556; MFE T+5=-0.004444444444444473; MAE T+5=-0.2866666666666666; MFE T+10=-0.004444444444444473; MAE T+10=-0.42666666666666664
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: lowest available T+10 forward returns; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
### A2-30 — 6668 — 2025-03-28

- Ticker: 6668
- Name: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS
- Anchor: 2025-03-28
- Historical bucket: FAILURE_CLEAR
- Historical A2 label: HISTORICAL_A2_EVENT
- Historical outcome label/proxy: REVIEW_FAILURE_PROXY
- Why machine considered this A2: formation_rule=L1 Close(T) >= MA60(T), mature reference, and Close(T) > Reference(T); close=54.4; ma60=51.1575; close_gt_ma60=PASS; reference=54.0; close_gt_reference=PASS; reference_policy_id=PRIOR_20_ACCEPTED_SESSION_HIGH; reference_birth_session=2025-02-27; reference_age_sessions=20; reference_maturity=PASS; gap_up=False; formation_match=True; classification_source=reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-expanded-event-panel.csv + reports/TASK-WS3-P2E-A2-EXPANDED-CONFIRMATORY-VALIDATION-AND-ADVANTAGE-REVALIDATION-20260820/ws3-p2e-a2-frozen-contract-manifest.json
- Current MA60 eligibility: PASS
- Anchor technical snapshot: D0 close=54.4; MA60=51.1575; distance_from_MA60=0.06338269071006208; volume=1650703.0; reference=54.0; reference_age_sessions=20; gap_up=False
- Pre-anchor context: D-20/D-10/D-5/D-3/D-1: NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS; D0 close=54.4; MA60=51.1575; distance_from_MA60=0.06338269071006208; volume=1650703.0; reference=54.0; reference_age_sessions=20; gap_up=False
- Forward outcome: T+1=-0.05698529411764708; T+3=-0.05882352941176461; T+5=-0.2371323529411764; T+10=-0.38511029411764697; MFE T+5=0.014705882352941346; MAE T+5=-0.2371323529411764; MFE T+10=0.014705882352941346; MAE T+10=-0.4283088235294117
- Machine historical interpretation: REVIEW_FAILURE_PROXY; Outcome-only proxy: lowest available T+10 forward returns; no setup judgment inferred.

OWNER REVIEW:

Setup validity: [ ] LEGITIMATE_A2  [ ] NOT_A2  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Outcome validity: [ ] SUCCESS  [ ] FAILURE  [ ] AMBIGUOUS  [ ] OWNER_REVIEW_REQUIRED
Visual setup family: [ ] A-like breakout  [ ] B-like re-strengthening  [ ] ordinary consolidation  [ ] downtrend / ineligible  [ ] late-stage extension  [ ] other
Owner notes: ________________________________________________
