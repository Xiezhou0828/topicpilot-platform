# WS3 A-like success vs false-friend comparisons

These comparisons use only the deterministic intermediate manifest. Same-looking and different-looking components are descriptive checklists for Owner review; they are not ranked discriminators, causal explanations, thresholds, or strategy rules.

## 1. `A|5c4bdf3475f1ed2b75af7cc01126adcd323f73699c374288cc0db3d132b86ec9|T5_GE_3`

- False friend: `4807` / `050ea7a6-771f-49f1-bf1f-14d617d37f84` on `2024-11-12`; market `TPE`; stratum `T5_GE_3`.
- Comparator: `4919` / `3df8ef0b-75c4-467c-99b1-0c2f807a7b65` on `2024-11-12`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-28.99%`, T+10 `-36.16%`, MFE/MAE T5 `3.37%`/`-28.99%`.
- Comparator outcome: T+5 `6.48%`, T+10 `5.68%`, MFE/MAE T5 `14.20%`/`-0.11%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `trend_background, improving_trend, base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.1965 MA20slope=0.05147; compression range20=0.2496 ratio=0.6357; volume ratio20=1.338 contraction=False expansion=True; momentum raw5=0.1288 RSI=73.1 MACD=0.4524; A-state=NEITHER | trend close/MA20=0.04367 MA20slope=0.007599; compression range20=0.1399 ratio=0.45; volume ratio20=0.7875 contraction=True expansion=False; momentum raw5=0.03373 RSI=57.4 MACD=0.5472; A-state=NEITHER |
| D-10 | trend close/MA20=0.04855 MA20slope=0.04831; compression range20=0.3971 ratio=0.2864; volume ratio20=0.5602 contraction=True expansion=False; momentum raw5=-0.02977 RSI=58.97 MACD=-0.2122; A-state=NEITHER | trend close/MA20=0.09309 MA20slope=0.03155; compression range20=0.234 ratio=0.8318; volume ratio20=2.828 contraction=False expansion=True; momentum raw5=0.1033 RSI=64.32 MACD=1.434; A-state=NEITHER |
| D-5 | trend close/MA20=0.2669 MA20slope=0.0846; compression range20=0.3499 ratio=0.6929; volume ratio20=2.557 contraction=False expansion=True; momentum raw5=0.3105 RSI=78.04 MACD=0.5661; A-state=NEITHER | trend close/MA20=0.07159 MA20slope=0.04285; compression range20=0.2914 ratio=0.5357; volume ratio20=1.212 contraction=False expansion=True; momentum raw5=0.02234 RSI=58.36 MACD=1.011; A-state=NEITHER |
| D-3 | trend close/MA20=0.1672 MA20slope=0.08968; compression range20=0.4725 ratio=0.7147; volume ratio20=0.6574 contraction=True expansion=False; momentum raw5=0.2063 RSI=69.77 MACD=0.5801; A-state=NEITHER | trend close/MA20=0.01745 MA20slope=0.0321; compression range20=0.304 ratio=0.45; volume ratio20=0.448 contraction=True expansion=False; momentum raw5=-0.08812 RSI=52.54 MACD=0.01372; A-state=NEITHER |
| D-1 | trend close/MA20=0.08505 MA20slope=0.07817; compression range20=0.4216 ratio=0.5776; volume ratio20=0.3794 contraction=True expansion=False; momentum raw5=-0.004545 RSI=62.19 MACD=0.2384; A-state=NEITHER | trend close/MA20=5.459e-05 MA20slope=0.02887; compression range20=0.2948 ratio=0.3481; volume ratio20=0.3181 contraction=True expansion=False; momentum raw5=-0.03376 RSI=51.48 MACD=-0.4516; A-state=NEITHER |
| D0 | trend close/MA20=0.1167 MA20slope=0.06727; compression range20=0.4056 ratio=0.5776; volume ratio20=1.026 contraction=False expansion=True; momentum raw5=-0.05923 RSI=65.2 MACD=0.2032; A-state=NEITHER | trend close/MA20=-0.0404 MA20slope=0.02258; compression range20=0.2898 ratio=0.3059; volume ratio20=0.3385 contraction=True expansion=False; momentum raw5=-0.08429 RSI=46.36 MACD=-0.8467; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 2. `A|54f4f887a3f86ecb65a9e6bed1a54c64ae59a8c3772cb12c5c09a503e93fd4d0|T5_GE_3`

- False friend: `4566` / `06833556-8e76-4893-b49f-1cec4e82756f` on `2025-11-24`; market `TPE`; stratum `T5_GE_3`.
- Comparator: `1563` / `b37722f3-572d-4324-976e-860e6b602c59` on `2025-11-24`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.38%`, T+10 `1.53%`, MFE/MAE T5 `6.30%`/`-0.76%`.
- Comparator outcome: T+5 `3.19%`, T+10 `0.98%`, MFE/MAE T5 `5.27%`/`-1.10%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `trend_background, base_compression, volume_contraction, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `improving_trend`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.02936 MA20slope=0.01141; compression range20=0.1635 ratio=0.3617; volume ratio20=1.12 contraction=False expansion=True; momentum raw5=0.0195 RSI=52.44 MACD=0.5368; A-state=A1_TO_A2 | trend close/MA20=0.01075 MA20slope=-0.008827; compression range20=0.1095 ratio=0.6286; volume ratio20=0.472 contraction=True expansion=False; momentum raw5=0.02567 RSI=50.1 MACD=0.2775; A-state=NEITHER |
| D-10 | trend close/MA20=-0.05627 MA20slope=-0.002221; compression range20=0.1774 ratio=0.3617; volume ratio20=0.3969 contraction=True expansion=False; momentum raw5=-0.04332 RSI=34.97 MACD=-0.4165; A-state=A1_TO_A2 | trend close/MA20=-0.07285 MA20slope=-0.01469; compression range20=0.1638 ratio=0.5603; volume ratio20=0.9617 contraction=True expansion=False; momentum raw5=-0.06616 RSI=22.9 MACD=-0.3843; A-state=NEITHER |
| D-5 | trend close/MA20=-0.03538 MA20slope=-0.01611; compression range20=0.1839 ratio=0.4286; volume ratio20=0.9804 contraction=True expansion=False; momentum raw5=0.00566 RSI=41.66 MACD=-0.1933; A-state=A1_TO_A2 | trend close/MA20=-0.05006 MA20slope=-0.01378; compression range20=0.1621 ratio=0.2908; volume ratio20=0.7617 contraction=True expansion=False; momentum raw5=0.01045 RSI=32.31 MACD=-0.1464; A-state=NEITHER |
| D-3 | trend close/MA20=-0.05155 MA20slope=-0.02373; compression range20=0.1896 ratio=0.4286; volume ratio20=1.509 contraction=False expansion=True; momentum raw5=-0.02268 RSI=35.97 MACD=-0.2104; A-state=A1_ONLY | trend close/MA20=-0.09191 MA20slope=-0.02064; compression range20=0.2156 ratio=0.4407; volume ratio20=1.465 contraction=False expansion=True; momentum raw5=-0.05524 RSI=22.99 MACD=-0.2766; A-state=NEITHER |
| D-1 | trend close/MA20=-0.02747 MA20slope=-0.02761; compression range20=0.187 ratio=0.3878; volume ratio20=2.18 contraction=False expansion=True; momentum raw5=-0.009452 RSI=40.97 MACD=-0.05901; A-state=NEITHER | trend close/MA20=-0.08125 MA20slope=-0.03248; compression range20=0.1995 ratio=0.5092; volume ratio20=1.408 contraction=False expansion=True; momentum raw5=-0.07264 RSI=22.69 MACD=-0.3003; A-state=NEITHER |
| D0 | trend close/MA20=-0.02284 MA20slope=-0.0295; compression range20=0.1393 ratio=0.5205; volume ratio20=0.4336 contraction=True expansion=False; momentum raw5=-0.01689 RSI=40.97 MACD=-0.01351; A-state=NEITHER | trend close/MA20=-0.07493 MA20slope=-0.03685; compression range20=0.1998 ratio=0.3436; volume ratio20=0.9222 contraction=True expansion=False; momentum raw5=-0.06207 RSI=22.52 MACD=-0.2775; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 3. `A|ba007d8d68876e5af5142c8858e2c987fcb8b2b1c2d1bef81870a35dd41140df|T10_GE_3`

- False friend: `3533` / `26fd9f8c-73bb-4aa3-abeb-1a9f0e6f5951` on `2024-12-13`; market `TPE`; stratum `T10_GE_3`.
- Comparator: `6409` / `96d7e0b7-bdf9-4a96-a419-c46d68cf4e4f` on `2024-12-13`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-3.11%`, T+10 `0.00%`, MFE/MAE T5 `2.33%`/`-5.70%`.
- Comparator outcome: T+5 `1.08%`, T+10 `3.52%`, MFE/MAE T5 `4.07%`/`-0.81%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_TO_A2`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `trend_background, improving_trend, participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.03576 MA20slope=0.01051; compression range20=0.1307 ratio=0.814; volume ratio20=1.094 contraction=False expansion=True; momentum raw5=-0.07584 RSI=47.2 MACD=-12.05; A-state=NEITHER | trend close/MA20=-0.09625 MA20slope=-0.02558; compression range20=0.2361 ratio=0.3371; volume ratio20=1.407 contraction=False expansion=True; momentum raw5=-0.05514 RSI=35.09 MACD=-32.6; A-state=NEITHER |
| D-10 | trend close/MA20=0.04343 MA20slope=0.0002915; compression range20=0.1061 ratio=0.9737; volume ratio20=1.737 contraction=False expansion=True; momentum raw5=0.01994 RSI=59.98 MACD=-4.834; A-state=A1_ONLY | trend close/MA20=-0.07106 MA20slope=-0.03047; compression range20=0.2364 ratio=0.6897; volume ratio20=1.522 contraction=False expansion=True; momentum raw5=-0.06599 RSI=36.4 MACD=-8.48; A-state=NEITHER |
| D-5 | trend close/MA20=0.09782 MA20slope=0.03541; compression range20=0.2026 ratio=0.4304; volume ratio20=1.099 contraction=False expansion=True; momentum raw5=0.08939 RSI=65.31 MACD=25.8; A-state=A1_TO_A2 | trend close/MA20=-0.01669 MA20slope=-0.03218; compression range20=0.1592 ratio=0.5667; volume ratio20=0.4355 contraction=True expansion=False; momentum raw5=0.02446 RSI=43.86 MACD=3.727; A-state=NEITHER |
| D-3 | trend close/MA20=0.05307 MA20slope=0.02741; compression range20=0.2095 ratio=0.3291; volume ratio20=0.862 contraction=True expansion=False; momentum raw5=-0.04071 RSI=58.26 MACD=13.28; A-state=A1_TO_A2 | trend close/MA20=0.01447 MA20slope=-0.01452; compression range20=0.1542 ratio=0.4833; volume ratio20=0.5296 contraction=True expansion=False; momentum raw5=0.07756 RSI=49.04 MACD=10.26; A-state=NEITHER |
| D-1 | trend close/MA20=0.05467 MA20slope=0.02447; compression range20=0.2068 ratio=0.2658; volume ratio20=0.6576 contraction=True expansion=False; momentum raw5=-0.03778 RSI=58.74 MACD=6.181; A-state=A1_TO_A2 | trend close/MA20=0.003771 MA20slope=0.00013; compression range20=0.1554 ratio=0.5667; volume ratio20=1.148 contraction=False expansion=True; momentum raw5=-0.01026 RSI=47.79 MACD=14.84; A-state=NEITHER |
| D0 | trend close/MA20=0.05739 MA20slope=0.02759; compression range20=0.2047 ratio=0.2658; volume ratio20=0.5582 contraction=True expansion=False; momentum raw5=-0.01026 RSI=60.16 MACD=3.535; A-state=A1_TO_A2 | trend close/MA20=-0.03944 MA20slope=0.001956; compression range20=0.1626 ratio=0.6; volume ratio20=0.9943 contraction=True expansion=False; momentum raw5=-0.02122 RSI=42.19 MACD=7.69; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 4. `A|1c0a75c2779ac40cebc4fedc4fba9433f3a1cbac113c4d11a203856c69deedd9|T5_GE_5`

- False friend: `1597` / `35d31c37-7336-4a9d-8e5e-1ea4ebcc24b9` on `2025-06-23`; market `TPE`; stratum `T5_GE_5`.
- Comparator: `3588` / `c2a814c3-8561-4f89-a64b-0b65a289c5f1` on `2025-06-23`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `1.21%`, T+10 `-3.03%`, MFE/MAE T5 `8.61%`/`1.09%`.
- Comparator outcome: T+5 `5.38%`, T+10 `3.14%`, MFE/MAE T5 `10.99%`/`0.90%`.
- Failure labels: `FAIL_T10_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `trend_background, improving_trend, base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.04032 MA20slope=0.08607; compression range20=0.3523 ratio=0.2984; volume ratio20=0.3225 contraction=True expansion=False; momentum raw5=-0.01974 RSI=57.02 MACD=0.7156; A-state=A1_ONLY | trend close/MA20=0.006466 MA20slope=0.013; compression range20=0.1245 ratio=0.272; volume ratio20=0.9282 contraction=True expansion=False; momentum raw5=-0.007905 RSI=49.43 MACD=0.2541; A-state=NEITHER |
| D-10 | trend close/MA20=-0.02586 MA20slope=0.01926; compression range20=0.1579 ratio=0.5507; volume ratio20=0.1645 contraction=True expansion=False; momentum raw5=0.01746 RSI=51.14 MACD=-0.5945; A-state=A1_ONLY | trend close/MA20=-0.02275 MA20slope=-0.006259; compression range20=0.1279 ratio=0.5366; volume ratio20=0.8543 contraction=True expansion=False; momentum raw5=0.04338 RSI=45.25 MACD=0.0001194; A-state=NEITHER |
| D-5 | trend close/MA20=-0.02958 MA20slope=-0.00535; compression range20=0.1594 ratio=0.4565; volume ratio20=0.2304 contraction=True expansion=False; momentum raw5=-0.009153 RSI=48.36 MACD=-0.5617; A-state=A1_ONLY | trend close/MA20=-0.03458 MA20slope=-0.01722; compression range20=0.1081 ratio=0.5545; volume ratio20=0.5531 contraction=True expansion=False; momentum raw5=-0.02911 RSI=39.77 MACD=-0.07171; A-state=NEITHER |
| D-3 | trend close/MA20=-0.03153 MA20slope=-0.01442; compression range20=0.1167 ratio=0.63; volume ratio20=0.2695 contraction=True expansion=False; momentum raw5=-0.05304 RSI=46.37 MACD=-0.6891; A-state=NEITHER | trend close/MA20=-0.0109 MA20slope=-0.01608; compression range20=0.106 ratio=0.5545; volume ratio20=0.6039 contraction=True expansion=False; momentum raw5=-0.009356 RSI=45.52 MACD=0.0006562; A-state=NEITHER |
| D-1 | trend close/MA20=-0.05316 MA20slope=-0.02023; compression range20=0.1386 ratio=0.4348; volume ratio20=0.4769 contraction=True expansion=False; momentum raw5=-0.04598 RSI=40.58 MACD=-0.9081; A-state=NEITHER | trend close/MA20=-0.04772 MA20slope=-0.01621; compression range20=0.1275 ratio=0.569; volume ratio20=1.147 contraction=False expansion=True; momentum raw5=-0.02151 RSI=36.44 MACD=-0.1175; A-state=NEITHER |
| D0 | trend close/MA20=-0.05515 MA20slope=-0.02157; compression range20=0.1697 ratio=0.5357; volume ratio20=0.2845 contraction=True expansion=False; momentum raw5=-0.04734 RSI=39.54 MACD=-0.9576; A-state=NEITHER | trend close/MA20=-0.06105 MA20slope=-0.01804; compression range20=0.1614 ratio=0.6806; volume ratio20=1.911 contraction=False expansion=True; momentum raw5=-0.04497 RSI=33.31 MACD=-0.2081; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 5. `A|6e71aba147e0c39c747d6a10200bfc8a231bfdaee3059f8c58b82419ee06cb98|T10_GE_3`

- False friend: `9904` / `872f5630-9648-4f3a-8319-7958017e3e3f` on `2025-12-09`; market `TPE`; stratum `T10_GE_3`.
- Comparator: `2034` / `753fcc63-203d-4e68-9746-2cc859b2ba12` on `2025-12-09`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `1.46%`, T+10 `-0.97%`, MFE/MAE T5 `2.76%`/`-0.49%`.
- Comparator outcome: T+5 `1.26%`, T+10 `3.53%`, MFE/MAE T5 `5.54%`/`-0.76%`.
- Failure labels: `FAIL_T10_NEGATIVE`; A-state false friend `A1_TO_A2`; comparator `A1_TO_A2`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `trend_background, base_compression, volume_contraction, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `improving_trend`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.008222 MA20slope=0.000943; compression range20=0.06908 ratio=0.5; volume ratio20=0.4027 contraction=True expansion=False; momentum raw5=0.01047 RSI=48.34 MACD=-0.05661; A-state=A1_TO_A2 | trend close/MA20=-0.03176 MA20slope=-0.007374; compression range20=0.164 ratio=0.2419; volume ratio20=0.4329 contraction=True expansion=False; momentum raw5=0 RSI=38.67 MACD=-0.06144; A-state=NEITHER |
| D-10 | trend close/MA20=0.01799 MA20slope=-0.0004261; compression range20=0.0804 ratio=0.3958; volume ratio20=0.6691 contraction=True expansion=False; momentum raw5=0.02577 RSI=56.71 MACD=0.03319; A-state=A1_ONLY | trend close/MA20=0.04021 MA20slope=-0.006187; compression range20=0.1022 ratio=0.7073; volume ratio20=1.177 contraction=False expansion=True; momentum raw5=0.03351 RSI=57.71 MACD=0.0957; A-state=A1_ONLY |
| D-5 | trend close/MA20=0.04149 MA20slope=0.01509; compression range20=0.09355 ratio=0.4138; volume ratio20=0.8287 contraction=True expansion=False; momentum raw5=0.03853 RSI=66.62 MACD=0.1546; A-state=A1_TO_A2 | trend close/MA20=0.05142 MA20slope=0.01647; compression range20=0.1602 ratio=0.4545; volume ratio20=0.9681 contraction=True expansion=False; momentum raw5=0.02743 RSI=61.23 MACD=0.1636; A-state=A1_TO_A2 |
| D-3 | trend close/MA20=0.04728 MA20slope=0.01765; compression range20=0.09236 ratio=0.4483; volume ratio20=0.6639 contraction=True expansion=False; momentum raw5=0.02614 RSI=69.93 MACD=0.1697; A-state=A1_TO_A2 | trend close/MA20=0.04464 MA20slope=0.02026; compression range20=0.1501 ratio=0.3226; volume ratio20=0.9247 contraction=True expansion=False; momentum raw5=0.004866 RSI=60.78 MACD=0.1268; A-state=A1_TO_A2 |
| D-1 | trend close/MA20=0.03057 MA20slope=0.01788; compression range20=0.09164 ratio=0.3333; volume ratio20=0.7629 contraction=True expansion=False; momentum raw5=0 RSI=63.43 MACD=0.1007; A-state=A1_TO_A2 | trend close/MA20=0.01056 MA20slope=0.01961; compression range20=0.1443 ratio=0.3103; volume ratio20=0.587 contraction=True expansion=False; momentum raw5=-0.02663 RSI=52.33 MACD=0.0447; A-state=A1_TO_A2 |
| D0 | trend close/MA20=0.01751 MA20slope=0.01697; compression range20=0.09091 ratio=0.5; volume ratio20=0.8474 contraction=True expansion=False; momentum raw5=-0.006452 RSI=58.45 MACD=0.05544; A-state=A1_TO_A2 | trend close/MA20=-0.004389 MA20slope=0.01761; compression range20=0.1461 ratio=0.3448; volume ratio20=0.794 contraction=True expansion=False; momentum raw5=-0.03641 RSI=48.8 MACD=6.989e-07; A-state=A1_TO_A2 |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 6. `A|312379cab80d4b60392411d0f30845427c84527007eaca1a3214eba1fe9356be|T10_GE_3`

- False friend: `3346` / `090ffa57-3150-4239-ab4c-9679da611924` on `2026-04-22`; market `TPE`; stratum `T10_GE_3`.
- Comparator: `3296` / `57bd9f79-c2d1-423a-9467-28386851d3a9` on `2026-04-22`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-5.45%`, T+10 `-6.27%`, MFE/MAE T5 `0.82%`/`-6.54%`.
- Comparator outcome: T+5 `-5.29%`, T+10 `6.73%`, MFE/MAE T5 `0.24%`/`-5.29%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `trend_background, base_compression, volume_contraction, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `improving_trend`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.05865 MA20slope=-0.01278; compression range20=0.1693 ratio=0.7656; volume ratio20=1.865 contraction=False expansion=True; momentum raw5=-0.03571 RSI=37.89 MACD=-0.02896; A-state=NEITHER | trend close/MA20=-0.05195 MA20slope=-0.02373; compression range20=0.178 ratio=0.3026; volume ratio20=0.789 contraction=True expansion=False; momentum raw5=-0.01613 RSI=33.71 MACD=-0.06158; A-state=NEITHER |
| D-10 | trend close/MA20=-0.04737 MA20slope=-0.02051; compression range20=0.1786 ratio=0.2154; volume ratio20=1.534 contraction=False expansion=True; momentum raw5=-0.01887 RSI=36.23 MACD=-0.07596; A-state=NEITHER | trend close/MA20=-0.009195 MA20slope=-0.007529; compression range20=0.08585 ratio=0.6486; volume ratio20=3.42 contraction=False expansion=True; momentum raw5=0.002326 RSI=39.87 MACD=0.08743; A-state=NEITHER |
| D-5 | trend close/MA20=-0.02933 MA20slope=-0.01858; compression range20=0.1896 ratio=0.2174; volume ratio20=1.169 contraction=False expansion=True; momentum raw5=0 RSI=39.05 MACD=0.0119; A-state=NEITHER | trend close/MA20=0.002773 MA20slope=-0.005057; compression range20=0.0553 ratio=0.7083; volume ratio20=0.62 contraction=True expansion=False; momentum raw5=0.006961 RSI=44.92 MACD=0.07512; A-state=NEITHER |
| D-3 | trend close/MA20=-0.004989 MA20slope=-0.02292; compression range20=0.1436 ratio=0.283; volume ratio20=0.9453 contraction=True expansion=False; momentum raw5=0.03073 RSI=43.61 MACD=0.07481; A-state=NEITHER | trend close/MA20=-0.01366 MA20slope=-0.00415; compression range20=0.05634 ratio=0.7083; volume ratio20=2.051 contraction=False expansion=True; momentum raw5=-0.009302 RSI=38.73 MACD=0.05059; A-state=NEITHER |
| D-1 | trend close/MA20=0.008975 MA20slope=-0.02311; compression range20=0.1132 ratio=0.2619; volume ratio20=1.282 contraction=False expansion=True; momentum raw5=0.0277 RSI=46.37 MACD=0.1032; A-state=NEITHER | trend close/MA20=-0.01415 MA20slope=-0.003928; compression range20=0.05647 ratio=0.7083; volume ratio20=1.61 contraction=False expansion=True; momentum raw5=-0.01163 RSI=37.95 MACD=0.02891; A-state=NEITHER |
| D0 | trend close/MA20=-0.0004086 MA20slope=-0.02093; compression range20=0.07629 ratio=0.3571; volume ratio20=1.267 contraction=False expansion=True; momentum raw5=0.008242 RSI=43.44 MACD=0.1037; A-state=NEITHER | trend close/MA20=-0.03379 MA20slope=-0.005199; compression range20=0.06731 ratio=0.75; volume ratio20=2.338 contraction=False expansion=True; momentum raw5=-0.04147 RSI=31.76 MACD=-0.004587; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 7. `A|2b56e81202bef583d115600d4da2a6f52faab2f1807bfa29770f28b94db535e2|T10_GE_5`

- False friend: `6243` / `1a19b207-ea85-48e1-b655-c8229410e4cb` on `2025-01-14`; market `TPE`; stratum `T10_GE_5`.
- Comparator: `2546` / `985eae41-8557-4398-87ae-f270a98aae8a` on `2025-01-14`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-4.63%`, T+10 `3.16%`, MFE/MAE T5 `0.56%`/`-5.08%`.
- Comparator outcome: T+5 `1.90%`, T+10 `5.42%`, MFE/MAE T5 `2.20%`/`0.00%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `trend_background, base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `improving_trend, participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.01726 MA20slope=0.006849; compression range20=0.2428 ratio=0.6298; volume ratio20=2.626 contraction=False expansion=True; momentum raw5=-0.09533 RSI=44.92 MACD=0.002273; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.04187 MA20slope=-0.005936; compression range20=0.08263 ratio=0.5932; volume ratio20=1.076 contraction=False expansion=True; momentum raw5=-0.0543 RSI=36.12 MACD=-0.4824; A-state=A1_TO_A2 |
| D-10 | trend close/MA20=-0.03221 MA20slope=0.0007129; compression range20=0.2376 ratio=0.3274; volume ratio20=0.2777 contraction=True expansion=False; momentum raw5=-0.03255 RSI=43.78 MACD=-0.08499; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.02079 MA20slope=-0.01608; compression range20=0.1165 ratio=0.2195; volume ratio20=0.4857 contraction=True expansion=False; momentum raw5=0.01004 RSI=41.16 MACD=-0.05953; A-state=A1_ONLY |
| D-5 | trend close/MA20=-0.03634 MA20slope=-0.02; compression range20=0.195 ratio=0.2541; volume ratio20=0.269 contraction=True expansion=False; momentum raw5=-0.02419 RSI=39.86 MACD=-0.1898; A-state=NEITHER | trend close/MA20=-0.01184 MA20slope=-0.01892; compression range20=0.09326 ratio=0.4308; volume ratio20=0.7815 contraction=True expansion=False; momentum raw5=-0.009943 RSI=41.93 MACD=0.09155; A-state=A1_ONLY |
| D-3 | trend close/MA20=-0.02103 MA20slope=-0.029; compression range20=0.13 ratio=0.2397; volume ratio20=0.6124 contraction=True expansion=False; momentum raw5=-0.001073 RSI=42.03 MACD=-0.1343; A-state=NEITHER | trend close/MA20=-0.01212 MA20slope=-0.01696; compression range20=0.06494 ratio=0.6; volume ratio20=1.434 contraction=False expansion=True; momentum raw5=-0.01702 RSI=40.23 MACD=0.0686; A-state=NEITHER |
| D-1 | trend close/MA20=-0.07122 MA20slope=-0.02665; compression range20=0.179 ratio=0.4395; volume ratio20=0.56 contraction=True expansion=False; momentum raw5=-0.05087 RSI=31.19 MACD=-0.2233; A-state=NEITHER | trend close/MA20=-0.02858 MA20slope=-0.01454; compression range20=0.07375 ratio=0.62; volume ratio20=1.683 contraction=False expansion=True; momentum raw5=-0.03966 RSI=34.2 MACD=-0.04457; A-state=NEITHER |
| D0 | trend close/MA20=-0.05861 MA20slope=-0.02378; compression range20=0.1751 ratio=0.5226; volume ratio20=0.232 contraction=True expansion=False; momentum raw5=-0.04634 RSI=33.92 MACD=-0.2586; A-state=NEITHER | trend close/MA20=-0.01924 MA20slope=-0.01269; compression range20=0.06735 ratio=0.6957; volume ratio20=0.6844 contraction=True expansion=False; momentum raw5=-0.02009 RSI=37.62 MACD=-0.05262; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 8. `A|9bde4b0d2d82e167fece0747a3ef31248dad95cd3ad6d81b577425152716fdc0|T5_GE_5`

- False friend: `1402` / `250cb664-8122-4165-ad6c-726c488c0e2c` on `2026-03-10`; market `TPE`; stratum `T5_GE_5`.
- Comparator: `2501` / `dcb4fff4-3420-41e6-b6a1-618ff53f68e7` on `2026-03-10`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-5.42%`, T+10 `-8.74%`, MFE/MAE T5 `0.87%`/`-5.59%`.
- Comparator outcome: T+5 `6.59%`, T+10 `7.27%`, MFE/MAE T5 `7.05%`/`1.36%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_ONLY`; comparator `A1_TO_A2`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": false}`
- Same-looking components: `improving_trend, base_compression, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `trend_background, volume_contraction, participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.001414 MA20slope=0.005688; compression range20=0.06018 ratio=0.7059; volume ratio20=1.176 contraction=False expansion=True; momentum raw5=-0.005282 RSI=49.69 MACD=-0.01459; A-state=A1_TO_A2 | trend close/MA20=-0.02444 MA20slope=-0.0126; compression range20=0.1042 ratio=0.2979; volume ratio20=0.4264 contraction=True expansion=False; momentum raw5=-0.002212 RSI=42.55 MACD=-0.1159; A-state=A1_TO_A2 |
| D-10 | trend close/MA20=-0.002829 MA20slope=-0.001148; compression range20=0.0727 ratio=0.439; volume ratio20=1.786 contraction=False expansion=True; momentum raw5=-0.01399 RSI=49.97 MACD=-0.005034; A-state=A1_TO_A2 | trend close/MA20=0.0117 MA20slope=-0.01309; compression range20=0.07269 ratio=0.6667; volume ratio20=1.364 contraction=False expansion=True; momentum raw5=0.02022 RSI=52.26 MACD=0.04578; A-state=NEITHER |
| D-5 | trend close/MA20=0.02682 MA20slope=0.002122; compression range20=0.1512 ratio=0.8182; volume ratio20=2.143 contraction=False expansion=True; momentum raw5=0.03191 RSI=60.63 MACD=0.09979; A-state=A1_ONLY | trend close/MA20=0.03038 MA20slope=0.001337; compression range20=0.08423 ratio=0.6667; volume ratio20=1.146 contraction=False expansion=True; momentum raw5=0.01982 RSI=57.62 MACD=0.1305; A-state=A1_TO_A2 |
| D-3 | trend close/MA20=-0.01387 MA20slope=0.00115; compression range20=0.1577 ratio=0.875; volume ratio20=1.16 contraction=False expansion=True; momentum raw5=-0.01933 RSI=44.47 MACD=-0.004528; A-state=A1_ONLY | trend close/MA20=0.01235 MA20slope=0.002565; compression range20=0.08571 ratio=0.6923; volume ratio20=1.017 contraction=False expansion=True; momentum raw5=0 RSI=51 MACD=0.0755; A-state=A1_TO_A2 |
| D-1 | trend close/MA20=0.01199 MA20slope=0.001943; compression range20=0.1533 ratio=0.4318; volume ratio20=0.9366 contraction=True expansion=False; momentum raw5=-0.01544 RSI=52.68 MACD=0.03732; A-state=A1_ONLY | trend close/MA20=-0.02748 MA20slope=0.001225; compression range20=0.1144 ratio=0.96; volume ratio20=1.56 contraction=False expansion=True; momentum raw5=-0.06624 RSI=40.05 MACD=-0.001215; A-state=A1_TO_A2 |
| D0 | trend close/MA20=0.007841 MA20slope=0.001323; compression range20=0.1538 ratio=0.4318; volume ratio20=0.4851 contraction=True expansion=False; momentum raw5=-0.01718 RSI=51.67 MACD=0.02342; A-state=A1_ONLY | trend close/MA20=-0.01961 MA20slope=-0.001224; compression range20=0.1136 ratio=0.72; volume ratio20=0.7195 contraction=True expansion=False; momentum raw5=-0.04968 RSI=42.24 MACD=-0.03692; A-state=A1_TO_A2 |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 9. `A|cfec4afb7ae6bc76a914d670050e3dee5c0e6c70c45c8dbdc4d64fc31ed0145c|T5_GE_3`

- False friend: `5608` / `74a3d5e9-22da-468a-97e3-58f744b5b73e` on `2026-07-28`; market `TPE`; stratum `T5_GE_3`.
- Comparator: `6168` / `ac7a08d7-9bda-4aaa-9e47-5d4bbf4b6059` on `2026-07-28`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.75%`, T+10 `4.49%`, MFE/MAE T5 `0.37%`/`-4.12%`.
- Comparator outcome: T+5 `13.16%`, T+10 `13.63%`, MFE/MAE T5 `16.63%`/`-9.70%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `base_compression, volume_contraction, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `trend_background, improving_trend`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.04408 MA20slope=-0.001181; compression range20=0.106 ratio=0.5; volume ratio20=0.532 contraction=True expansion=False; momentum raw5=-0.04392 RSI=37.78 MACD=-0.06638; A-state=NEITHER | trend close/MA20=0.05533 MA20slope=0.03643; compression range20=0.4497 ratio=0.5336; volume ratio20=0.5751 contraction=True expansion=False; momentum raw5=-0.0418 RSI=53.23 MACD=0.392; A-state=A2_WITHOUT_PRIOR_A1 |
| D-10 | trend close/MA20=-0.03309 MA20slope=-0.007149; compression range20=0.1064 ratio=0.7; volume ratio20=1.397 contraction=False expansion=True; momentum raw5=-0.05686 RSI=40.51 MACD=-0.007095; A-state=NEITHER | trend close/MA20=-0.1041 MA20slope=0.03336; compression range20=0.4115 ratio=0.5113; volume ratio20=0.3633 contraction=True expansion=False; momentum raw5=-0.102 RSI=42.77 MACD=-0.4747; A-state=A2_WITHOUT_PRIOR_A1 |
| D-5 | trend close/MA20=-0.0335 MA20slope=-0.01732; compression range20=0.1444 ratio=0.575; volume ratio20=0.7292 contraction=True expansion=False; momentum raw5=-0.01773 RSI=41.13 MACD=-0.07544; A-state=NEITHER | trend close/MA20=-0.1718 MA20slope=-0.02703; compression range20=0.559 ratio=0.3926; volume ratio20=0.1596 contraction=True expansion=False; momentum raw5=-0.1006 RSI=37.23 MACD=-0.7757; A-state=A2_WITHOUT_PRIOR_A1 |
| D-3 | trend close/MA20=-0.04211 MA20slope=-0.0186; compression range20=0.1465 ratio=0.425; volume ratio20=0.9052 contraction=True expansion=False; momentum raw5=-0.04545 RSI=38.46 MACD=-0.06778; A-state=NEITHER | trend close/MA20=-0.1434 MA20slope=-0.05903; compression range20=0.5021 ratio=0.2397; volume ratio20=0.299 contraction=True expansion=False; momentum raw5=-0.09907 RSI=38.43 MACD=-0.6339; A-state=NEITHER |
| D-1 | trend close/MA20=-0.03772 MA20slope=-0.01339; compression range20=0.1465 ratio=0.275; volume ratio20=0.7093 contraction=True expansion=False; momentum raw5=0.003676 RSI=39.12 MACD=-0.05211; A-state=NEITHER | trend close/MA20=-0.1442 MA20slope=-0.07337; compression range20=0.4103 ratio=0.2812; volume ratio20=0.4525 contraction=True expansion=False; momentum raw5=-0.008475 RSI=36.53 MACD=-0.5521; A-state=NEITHER |
| D0 | trend close/MA20=-0.0562 MA20slope=-0.01291; compression range20=0.1573 ratio=0.381; volume ratio20=0.8322 contraction=True expansion=False; momentum raw5=-0.0361 RSI=35.14 MACD=-0.06332; A-state=NEITHER | trend close/MA20=-0.1962 MA20slope=-0.0763; compression range20=0.5012 ratio=0.3641; volume ratio20=0.4775 contraction=True expansion=False; momentum raw5=-0.1035 RSI=32.12 MACD=-0.6033; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 10. `A|3ff9507dd20702aeb149a94d19b7a3cc8d031c9938f41bc25bba4345885359d2|T5_GE_3`

- False friend: `6173` / `1ec4ef18-d868-486d-b151-cd3cbbcc55f9` on `2024-11-12`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `6175` / `fee85b28-d0a5-452e-9c25-a46d65d9c19e` on `2024-11-12`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-2.06%`, T+10 `0.00%`, MFE/MAE T5 `0.69%`/`-3.43%`.
- Comparator outcome: T+5 `8.60%`, T+10 `10.40%`, MFE/MAE T5 `13.45%`/`0.55%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `base_compression, volume_contraction, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `trend_background, improving_trend`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.002716 MA20slope=0.01328; compression range20=0.1167 ratio=0.3661; volume ratio20=0.5651 contraction=True expansion=False; momentum raw5=0.006289 RSI=51.7 MACD=0.03499; A-state=NEITHER | trend close/MA20=-0.007572 MA20slope=-0.00578; compression range20=0.06131 ratio=0.8; volume ratio20=0.7164 contraction=True expansion=False; momentum raw5=-0.009447 RSI=41.52 MACD=0.0565; A-state=NEITHER |
| D-10 | trend close/MA20=-0.01031 MA20slope=-0.0002604; compression range20=0.07158 ratio=0.3382; volume ratio20=0.9333 contraction=True expansion=False; momentum raw5=-0.01452 RSI=46.13 MACD=-0.0231; A-state=NEITHER | trend close/MA20=-0.02745 MA20slope=-0.006765; compression range20=0.07843 ratio=0.5893; volume ratio20=0.9532 contraction=True expansion=False; momentum raw5=-0.01653 RSI=35.18 MACD=-0.01651; A-state=NEITHER |
| D-5 | trend close/MA20=-0.05139 MA20slope=-0.0138; compression range20=0.1136 ratio=0.7157; volume ratio20=0.6302 contraction=True expansion=False; momentum raw5=-0.05474 RSI=30.31 MACD=-0.3553; A-state=NEITHER | trend close/MA20=-0.04325 MA20slope=-0.01907; compression range20=0.1016 ratio=0.4286; volume ratio20=0.5004 contraction=True expansion=False; momentum raw5=-0.03501 RSI=28.39 MACD=-0.1209; A-state=NEITHER |
| D-3 | trend close/MA20=-0.02823 MA20slope=-0.01451; compression range20=0.1083 ratio=0.3737; volume ratio20=1.004 contraction=False expansion=True; momentum raw5=0.01218 RSI=39.63 MACD=-0.2643; A-state=NEITHER | trend close/MA20=-0.02064 MA20slope=-0.01894; compression range20=0.1029 ratio=0.2778; volume ratio20=1.141 contraction=False expansion=True; momentum raw5=0.008646 RSI=38.8 MACD=-0.06581; A-state=NEITHER |
| D-1 | trend close/MA20=-0.0437 MA20slope=-0.01538; compression range20=0.104 ratio=0.3441; volume ratio20=0.4331 contraction=True expansion=False; momentum raw5=-0.008869 RSI=33.51 MACD=-0.2319; A-state=NEITHER | trend close/MA20=-0.027 MA20slope=-0.01598; compression range20=0.09104 ratio=0.3492; volume ratio20=1.029 contraction=False expansion=True; momentum raw5=0 RSI=36.2 MACD=-0.02712; A-state=NEITHER |
| D0 | trend close/MA20=-0.06077 MA20slope=-0.01701; compression range20=0.1133 ratio=0.4444; volume ratio20=1.238 contraction=False expansion=True; momentum raw5=-0.02673 RSI=28.48 MACD=-0.2687; A-state=NEITHER | trend close/MA20=0.01471 MA20slope=-0.01333; compression range20=0.0957 ratio=1; volume ratio20=4.978 contraction=False expansion=True; momentum raw5=0.04644 RSI=52.43 MACD=0.08848; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 11. `A|0f82e81f67f452a3ca91b47e2cde7b7c711a42a7b27ce894eed3220ae0cecb69|T10_GE_3`

- False friend: `3527` / `174b02a0-a52b-4663-a5ca-78d41bbd64f9` on `2026-07-21`; market `TWO`; stratum `T10_GE_3`.
- Comparator: `6530` / `df6aa862-dec4-4433-8770-b65a2932ea03` on `2026-07-21`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-11.02%`, T+10 `-12.37%`, MFE/MAE T5 `1.19%`/`-11.02%`.
- Comparator outcome: T+5 `-1.29%`, T+10 `7.02%`, MFE/MAE T5 `11.17%`/`-1.29%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_ONLY`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `improving_trend, base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `trend_background, participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.1445 MA20slope=0.04569; compression range20=0.2621 ratio=0.7554; volume ratio20=1.607 contraction=False expansion=True; momentum raw5=0.1818 RSI=67.28 MACD=1.302; A-state=A1_TO_A2 | trend close/MA20=-0.04862 MA20slope=-0.01859; compression range20=0.2708 ratio=0.2815; volume ratio20=0.6145 contraction=True expansion=False; momentum raw5=0.02467 RSI=45.55 MACD=-0.843; A-state=NEITHER |
| D-10 | trend close/MA20=0.0331 MA20slope=0.02294; compression range20=0.2754 ratio=0.3315; volume ratio20=1.47 contraction=False expansion=True; momentum raw5=0.04375 RSI=57.48 MACD=-0.278; A-state=A1_TO_A2 | trend close/MA20=-0.06882 MA20slope=-0.06255; compression range20=0.2794 ratio=0.2727; volume ratio20=0.6747 contraction=True expansion=False; momentum raw5=0.01643 RSI=38.96 MACD=-0.3962; A-state=NEITHER |
| D-5 | trend close/MA20=-0.08571 MA20slope=0.01322; compression range20=0.2588 ratio=0.5355; volume ratio20=0.435 contraction=True expansion=False; momentum raw5=-0.1033 RSI=41.63 MACD=-0.826; A-state=A1_TO_A2 | trend close/MA20=-0.1347 MA20slope=-0.04935; compression range20=0.3778 ratio=0.737; volume ratio20=1.102 contraction=False expansion=True; momentum raw5=-0.1166 RSI=29.53 MACD=-0.5292; A-state=NEITHER |
| D-3 | trend close/MA20=-0.09098 MA20slope=-0.004532; compression range20=0.2632 ratio=0.4129; volume ratio20=0.2365 contraction=True expansion=False; momentum raw5=-0.06359 RSI=39.82 MACD=-0.9202; A-state=A1_ONLY | trend close/MA20=-0.1374 MA20slope=-0.05156; compression range20=0.3745 ratio=0.4624; volume ratio20=0.5655 contraction=True expansion=False; momentum raw5=-0.1131 RSI=28.25 MACD=-0.6437; A-state=NEITHER |
| D-1 | trend close/MA20=-0.1458 MA20slope=-0.03474; compression range20=0.387 ratio=0.4211; volume ratio20=0.6046 contraction=True expansion=False; momentum raw5=-0.1248 RSI=31.53 MACD=-1.343; A-state=A1_ONLY | trend close/MA20=-0.1827 MA20slope=-0.06579; compression range20=0.5344 ratio=0.4466; volume ratio20=0.6335 contraction=True expansion=False; momentum raw5=-0.1365 RSI=23.7 MACD=-1.106; A-state=NEITHER |
| D0 | trend close/MA20=-0.05834 MA20slope=-0.04365; compression range20=0.3034 ratio=0.4413; volume ratio20=1.177 contraction=False expansion=True; momentum raw5=-0.01503 RSI=44.98 MACD=-1.042; A-state=A1_ONLY | trend close/MA20=-0.1495 MA20slope=-0.07171; compression range20=0.5158 ratio=0.3889; volume ratio20=0.4452 contraction=True expansion=False; momentum raw5=-0.08758 RSI=26.97 MACD=-0.9843; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 12. `A|5d820f0c9a0b17a471dabb7bbd4a246c2731f79375082b2dbf75578841cee6f5|T5_GE_3`

- False friend: `5483` / `76695cfa-e9cd-43a3-a929-07cf418f381a` on `2025-08-06`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `4760` / `62f9ce93-d96e-4312-af06-487a0fcda9b6` on `2025-08-06`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-1.29%`, T+10 `0.99%`, MFE/MAE T5 `8.91%`/`-2.77%`.
- Comparator outcome: T+5 `5.02%`, T+10 `2.70%`, MFE/MAE T5 `6.56%`/`-2.70%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `A1_TO_A2`; comparator `A1_TO_A2`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `trend_background, improving_trend, base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.02987 MA20slope=-0.002068; compression range20=0.1362 ratio=0.4545; volume ratio20=0.6133 contraction=True expansion=False; momentum raw5=0.01893 RSI=49.96 MACD=0.9511; A-state=NEITHER | trend close/MA20=0.08648 MA20slope=0.002207; compression range20=0.1802 ratio=0.65; volume ratio20=8.323 contraction=False expansion=True; momentum raw5=0.06731 RSI=67.94 MACD=0.8731; A-state=A1_TO_A2 |
| D-10 | trend close/MA20=0.1002 MA20slope=0.05306; compression range20=0.2374 ratio=0.5192; volume ratio20=0.6741 contraction=True expansion=False; momentum raw5=0.0961 RSI=63.9 MACD=2.025; A-state=A1_TO_A2 | trend close/MA20=0.2332 MA20slope=0.09161; compression range20=0.3798 ratio=0.6697; volume ratio20=3.701 contraction=False expansion=True; momentum raw5=0.2213 RSI=73.79 MACD=3.543; A-state=A1_TO_A2 |
| D-5 | trend close/MA20=-0.004198 MA20slope=0.02914; compression range20=0.2206 ratio=0.4; volume ratio20=0.7882 contraction=True expansion=False; momentum raw5=-0.06849 RSI=49.07 MACD=-0.09104; A-state=A1_TO_A2 | trend close/MA20=0.1111 MA20slope=0.08285; compression range20=0.3714 ratio=0.3269; volume ratio20=2.279 contraction=False expansion=True; momentum raw5=-0.02439 RSI=65.91 MACD=0.7567; A-state=A1_TO_A2 |
| D-3 | trend close/MA20=-0.008361 MA20slope=0.01968; compression range20=0.2206 ratio=0.4356; volume ratio20=0.3304 contraction=True expansion=False; momentum raw5=-0.05116 RSI=49.28 MACD=-0.5742; A-state=A1_TO_A2 | trend close/MA20=0.07032 MA20slope=0.07288; compression range20=0.3755 ratio=0.3269; volume ratio20=0.3442 contraction=True expansion=False; momentum raw5=-0.01773 RSI=63.91 MACD=-0.1365; A-state=A1_TO_A2 |
| D-1 | trend close/MA20=-0.001592 MA20slope=0.01548; compression range20=0.2068 ratio=0.3178; volume ratio20=0.4525 contraction=True expansion=False; momentum raw5=0.004854 RSI=52.41 MACD=-0.5875; A-state=A1_TO_A2 | trend close/MA20=0.06968 MA20slope=0.06884; compression range20=0.3169 ratio=0.3778; volume ratio20=0.5218 contraction=True expansion=False; momentum raw5=0.02527 RSI=63.88 MACD=-0.7003; A-state=A1_TO_A2 |
| D0 | trend close/MA20=-0.02763 MA20slope=0.01406; compression range20=0.205 ratio=0.3285; volume ratio20=0.4009 contraction=True expansion=False; momentum raw5=-0.009804 RSI=47.18 MACD=-0.6904; A-state=A1_TO_A2 | trend close/MA20=-0.03123 MA20slope=0.06091; compression range20=0.3205 ratio=0.3253; volume ratio20=1.064 contraction=False expansion=True; momentum raw5=-0.075 RSI=51.06 MACD=-1.468; A-state=A1_TO_A2 |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 13. `A|b0ae649b4892d70e8f797dcdf4d7e0baf0fe11724429ad5ed4cc53c37c7f5e4d|T5_GE_5`

- False friend: `6290` / `b6624814-8ba4-4e16-a7e5-797c20612669` on `2026-03-09`; market `TWO`; stratum `T5_GE_5`.
- Comparator: `6274` / `264a29cf-b29f-464b-b291-cc176ce3c892` on `2026-03-09`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `3.01%`, T+10 `-1.39%`, MFE/MAE T5 `5.56%`/`-6.71%`.
- Comparator outcome: T+5 `10.79%`, T+10 `18.50%`, MFE/MAE T5 `14.54%`/`-2.86%`.
- Failure labels: `FAIL_T10_NEGATIVE`; A-state false friend `A2_WITHOUT_PRIOR_A1`; comparator `A1_TO_A2`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": false}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`
- Same-looking components: `trend_background, improving_trend, base_compression, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `volume_contraction`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.01849 MA20slope=-0.01802; compression range20=0.1721 ratio=0.3276; volume ratio20=0.5545 contraction=True expansion=False; momentum raw5=0.00597 RSI=45.12 MACD=-0.06622; A-state=NEITHER | trend close/MA20=0.1095 MA20slope=0.01298; compression range20=0.1763 ratio=0.8632; volume ratio20=1.151 contraction=False expansion=True; momentum raw5=0.1641 RSI=70.66 MACD=4.021; A-state=A1_ONLY |
| D-10 | trend close/MA20=0.09134 MA20slope=0.01614; compression range20=0.1941 ratio=0.9306; volume ratio20=2.091 contraction=False expansion=True; momentum raw5=0.08798 RSI=60.87 MACD=2.553; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=0.04998 MA20slope=0.02618; compression range20=0.1786 ratio=0.5579; volume ratio20=0.5816 contraction=True expansion=False; momentum raw5=-0.009311 RSI=61.11 MACD=0.4878; A-state=A1_ONLY |
| D-5 | trend close/MA20=0.1771 MA20slope=0.06457; compression range20=0.3592 ratio=0.5229; volume ratio20=1.666 contraction=False expansion=True; momentum raw5=0.1482 RSI=66.3 MACD=5.626; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=0.0271 MA20slope=0.03765; compression range20=0.2093 ratio=0.5575; volume ratio20=0.952 contraction=True expansion=False; momentum raw5=0.01504 RSI=57.12 MACD=0.8923; A-state=A1_TO_A2 |
| D-3 | trend close/MA20=0.1595 MA20slope=0.06966; compression range20=0.3558 ratio=0.4118; volume ratio20=1.617 contraction=False expansion=True; momentum raw5=0.02381 RSI=66.63 MACD=4.373; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.07045 MA20slope=0.02846; compression range20=0.1947 ratio=1; volume ratio20=1.296 contraction=False expansion=True; momentum raw5=-0.1272 RSI=43.06 MACD=-4.356; A-state=A1_TO_A2 |
| D-1 | trend close/MA20=0.2448 MA20slope=0.07682; compression range20=0.3674 ratio=0.4886; volume ratio20=1.566 contraction=False expansion=True; momentum raw5=0.05507 RSI=74.7 MACD=5.208; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.04196 MA20slope=0.008; compression range20=0.1895 ratio=0.7487; volume ratio20=1.558 contraction=False expansion=True; momentum raw5=-0.07523 RSI=46.93 MACD=-6.65; A-state=A1_TO_A2 |
| D0 | trend close/MA20=0.109 MA20slope=0.0764; compression range20=0.4074 ratio=0.4886; volume ratio20=0.2163 contraction=True expansion=False; momentum raw5=0.01408 RSI=59 MACD=3.497; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.13 MA20slope=-0.007466; compression range20=0.2841 ratio=0.814; volume ratio20=0.6322 contraction=True expansion=False; momentum raw5=-0.1593 RSI=36.54 MACD=-10.16; A-state=A1_TO_A2 |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 14. `A|91246c0c22558c70be43381882fbfa649ff25d571dd2a0e92a6ada0c4b7df779|T5_GE_3`

- False friend: `5328` / `0982ffab-8f59-44cb-850e-12edde60be38` on `2025-06-30`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `5302` / `8c548e22-a7da-4824-9847-97ef8bbdaefe` on `2025-06-30`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-1.57%`, T+10 `-0.79%`, MFE/MAE T5 `2.36%`/`-1.97%`.
- Comparator outcome: T+5 `4.11%`, T+10 `1.17%`, MFE/MAE T5 `4.11%`/`0.15%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `trend_background, base_compression, volume_contraction, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `improving_trend, participation_transition`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.05244 MA20slope=0.002902; compression range20=0.1183 ratio=0.7419; volume ratio20=0.9065 contraction=True expansion=False; momentum raw5=-0.05755 RSI=37.66 MACD=-0.07018; A-state=NEITHER | trend close/MA20=-0.07268 MA20slope=-0.001565; compression range20=0.1592 ratio=0.7876; volume ratio20=1.475 contraction=False expansion=True; momentum raw5=-0.08031 RSI=32.2 MACD=-0.03367; A-state=NEITHER |
| D-10 | trend close/MA20=-0.03943 MA20slope=-0.02086; compression range20=0.1167 ratio=0.4667; volume ratio20=0.7876 contraction=True expansion=False; momentum raw5=-0.003876 RSI=38.03 MACD=-0.04791; A-state=NEITHER | trend close/MA20=-0.04413 MA20slope=-0.01931; compression range20=0.1307 ratio=0.3804; volume ratio20=1.184 contraction=False expansion=True; momentum raw5=-0.01538 RSI=33.65 MACD=-0.007336; A-state=NEITHER |
| D-5 | trend close/MA20=-0.06166 MA20slope=-0.02411; compression range20=0.1714 ratio=0.5238; volume ratio20=1.472 contraction=False expansion=True; momentum raw5=-0.04669 RSI=28.61 MACD=-0.06839; A-state=NEITHER | trend close/MA20=-0.0369 MA20slope=-0.02301; compression range20=0.1587 ratio=0.3455; volume ratio20=2.7 contraction=False expansion=True; momentum raw5=-0.01562 RSI=32.88 MACD=-0.003087; A-state=NEITHER |
| D-3 | trend close/MA20=-0.01893 MA20slope=-0.02468; compression range20=0.1575 ratio=0.5; volume ratio20=1.426 contraction=False expansion=True; momentum raw5=-0.0155 RSI=41.7 MACD=-0.02707; A-state=NEITHER | trend close/MA20=-0.03452 MA20slope=-0.02424; compression range20=0.1105 ratio=0.4211; volume ratio20=1.731 contraction=False expansion=True; momentum raw5=-0.02134 RSI=31.75 MACD=-0.00846; A-state=NEITHER |
| D-1 | trend close/MA20=0.00563 MA20slope=-0.01979; compression range20=0.1158 ratio=0.7333; volume ratio20=0.8228 contraction=True expansion=False; momentum raw5=0.04435 RSI=47.82 MACD=0.02776; A-state=NEITHER | trend close/MA20=-0.01977 MA20slope=-0.02142; compression range20=0.09942 ratio=0.4203; volume ratio20=0.529 contraction=True expansion=False; momentum raw5=-0.02116 RSI=36.04 MACD=0.0002616; A-state=NEITHER |
| D0 | trend close/MA20=-0.01225 MA20slope=-0.01513; compression range20=0.1102 ratio=0.4286; volume ratio20=0.6332 contraction=True expansion=False; momentum raw5=0.03673 RSI=42.63 MACD=0.02641; A-state=NEITHER | trend close/MA20=-0.03481 MA20slope=-0.018; compression range20=0.1012 ratio=0.3333; volume ratio20=1.961 contraction=False expansion=True; momentum raw5=-0.01587 RSI=31.7 MACD=-0.001847; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 15. `A|a36547894facabc68edba1b7589ae8026e7526dc4e45d073c0233780b5ee86ae|T5_GE_3`

- False friend: `8111` / `6327b249-d093-4117-92f7-1e948fe54b3b` on `2026-07-29`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `8358` / `7e3fd812-0aa2-4d3e-b246-e2f52392d341` on `2026-07-29`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `1.44%`, T+10 `-6.07%`, MFE/MAE T5 `10.22%`/`-13.26%`.
- Comparator outcome: T+5 `16.11%`, T+10 `39.04%`, MFE/MAE T5 `24.58%`/`-9.97%`.
- Failure labels: `FAIL_T10_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": false}`
- Comparator: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`
- Same-looking components: `trend_background, base_compression, participation_transition, breakout_context_proxy, ma_convergence_proxy`
- Different-looking components: `improving_trend, volume_contraction`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.0822 MA20slope=-0.05703; compression range20=0.3429 ratio=0.4022; volume ratio20=0.5337 contraction=True expansion=False; momentum raw5=-0.05606 RSI=34.93 MACD=-0.2918; A-state=NEITHER | trend close/MA20=-0.01607 MA20slope=0.00511; compression range20=0.4133 ratio=0.4556; volume ratio20=0.9934 contraction=True expansion=False; momentum raw5=-0.08676 RSI=52.53 MACD=-13.54; A-state=A2_WITHOUT_PRIOR_A1 |
| D-10 | trend close/MA20=-0.03947 MA20slope=-0.03248; compression range20=0.2465 ratio=0.5582; volume ratio20=1.337 contraction=False expansion=True; momentum raw5=-0.01367 RSI=39.86 MACD=0.01903; A-state=NEITHER | trend close/MA20=-0.2035 MA20slope=-0.03542; compression range20=0.6692 ratio=0.37; volume ratio20=0.5404 contraction=True expansion=False; momentum raw5=-0.1157 RSI=36.47 MACD=-19.42; A-state=A2_WITHOUT_PRIOR_A1 |
| D-5 | trend close/MA20=0.01902 MA20slope=-0.035; compression range20=0.2592 ratio=0.5672; volume ratio20=1.803 contraction=False expansion=True; momentum raw5=0.02376 RSI=48.67 MACD=0.2416; A-state=NEITHER | trend close/MA20=-0.1997 MA20slope=-0.1123; compression range20=0.7079 ratio=0.3493; volume ratio20=1.406 contraction=False expansion=True; momentum raw5=-0.1081 RSI=36.03 MACD=-18.09; A-state=NEITHER |
| D-3 | trend close/MA20=0.1849 MA20slope=-0.01658; compression range20=0.2954 ratio=1; volume ratio20=8.478 contraction=False expansion=True; momentum raw5=0.238 RSI=62.9 MACD=1.383; A-state=NEITHER | trend close/MA20=-0.2521 MA20slope=-0.1221; compression range20=0.7929 ratio=0.256; volume ratio20=0.8866 contraction=True expansion=False; momentum raw5=-0.07905 RSI=31.39 MACD=-14.47; A-state=NEITHER |
| D-1 | trend close/MA20=0.182 MA20slope=0.02691; compression range20=0.4029 ratio=0.8052; volume ratio20=8.678 contraction=False expansion=True; momentum raw5=0.3149 RSI=62.86 MACD=1.99; A-state=NEITHER | trend close/MA20=-0.2896 MA20slope=-0.109; compression range20=0.9132 ratio=0.3262; volume ratio20=1.084 contraction=False expansion=True; momentum raw5=-0.1534 RSI=28.74 MACD=-13.13; A-state=NEITHER |
| D0 | trend close/MA20=0.1855 MA20slope=0.0408; compression range20=0.3978 ratio=0.6426; volume ratio20=3.975 contraction=False expansion=True; momentum raw5=0.2108 RSI=63.88 MACD=2.027; A-state=NEITHER | trend close/MA20=-0.3388 MA20slope=-0.1168; compression range20=1.123 ratio=0.3447; volume ratio20=1.041 contraction=False expansion=True; momentum raw5=-0.2703 RSI=26.03 MACD=-14.36; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.
