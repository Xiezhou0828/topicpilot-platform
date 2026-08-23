# WS3 B-like success vs false-friend comparisons

These comparisons use only the deterministic intermediate manifest. Same-looking and different-looking components are descriptive checklists for Owner review; they are not ranked discriminators, causal explanations, thresholds, or strategy rules.

## 1. `B|514ba0b466dab688f328123c054b186896841ca3f1973197fed80a2b905518bf|T5_GE_3`

- False friend: `4807` / `050ea7a6-771f-49f1-bf1f-14d617d37f84` on `2024-11-14`; market `TPE`; stratum `T5_GE_3`.
- Comparator: `2465` / `c68ddcce-2c14-4d98-8ff2-fdd11f06d552` on `2024-11-14`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-35.44%`, T+10 `-39.22%`, MFE/MAE T5 `-9.95%`/`-36.20%`.
- Comparator outcome: T+5 `4.77%`, T+10 `0.72%`, MFE/MAE T5 `13.44%`/`-3.03%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Same-looking components: `prior_expansion, pullback, stabilization, reclaim_turn`
- Different-looking components: `trend_preservation`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.246 MA20slope=0.06421; compression range20=0.3765 ratio=0.7753; volume ratio20=3.807 contraction=False expansion=True; momentum raw5=0.1641 RSI=74.52 MACD=0.7415; A-state=NEITHER | trend close/MA20=-0.03903 MA20slope=0.002386; compression range20=0.1233 ratio=0.7103; volume ratio20=1.126 contraction=False expansion=True; momentum raw5=-0.09395 RSI=42.81 MACD=-0.0369; A-state=NEITHER |
| D-10 | trend close/MA20=0.05438 MA20slope=0.05617; compression range20=0.3759 ratio=0.4186; volume ratio20=1.327 contraction=False expansion=True; momentum raw5=0.0438 RSI=61.1 MACD=-0.1212; A-state=NEITHER | trend close/MA20=-0.001409 MA20slope=-0.01148; compression range20=0.1433 ratio=0.5433; volume ratio20=1.614 contraction=False expansion=True; momentum raw5=0.00113 RSI=50.14 MACD=0.07353; A-state=NEITHER |
| D-5 | trend close/MA20=0.1672 MA20slope=0.08968; compression range20=0.4725 ratio=0.7147; volume ratio20=0.6574 contraction=True expansion=False; momentum raw5=0.2063 RSI=69.77 MACD=0.5801; A-state=NEITHER | trend close/MA20=-0.02354 MA20slope=-0.03505; compression range20=0.2596 ratio=0.7281; volume ratio20=3.478 contraction=False expansion=True; momentum raw5=-0.05643 RSI=46.67 MACD=-0.4997; A-state=NEITHER |
| D-3 | trend close/MA20=0.08505 MA20slope=0.07817; compression range20=0.4216 ratio=0.5776; volume ratio20=0.3794 contraction=True expansion=False; momentum raw5=-0.004545 RSI=62.19 MACD=0.2384; A-state=NEITHER | trend close/MA20=-0.0747 MA20slope=-0.03658; compression range20=0.2548 ratio=0.794; volume ratio20=0.9683 contraction=True expansion=False; momentum raw5=0.03581 RSI=40.02 MACD=-0.5432; A-state=NEITHER |
| D-1 | trend close/MA20=0.09692 MA20slope=0.05476; compression range20=0.411 ratio=0.2455; volume ratio20=0.6542 contraction=True expansion=False; momentum raw5=-0.03022 RSI=63.32 MACD=0.1219; A-state=NEITHER | trend close/MA20=-0.1159 MA20slope=-0.0385; compression range20=0.2592 ratio=0.7842; volume ratio20=0.5217 contraction=True expansion=False; momentum raw5=-0.09282 RSI=34.87 MACD=-0.8312; A-state=NEITHER |
| D0 | trend close/MA20=0.07377 MA20slope=0.04449; compression range20=0.4178 ratio=0.2455; volume ratio20=0.8363 contraction=True expansion=False; momentum raw5=-0.03913 RSI=61 MACD=0.009388; A-state=NEITHER | trend close/MA20=-0.1564 MA20slope=-0.04193; compression range20=0.3237 ratio=0.6205; volume ratio20=1.36 contraction=False expansion=True; momentum raw5=-0.1722 RSI=31 MACD=-1.095; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 2. `B|330cddc8e96d3559db248e680e8b0a17a4db8f695fcbdc4be40ee818b6b22aa3|T5_GE_3`

- False friend: `2031` / `4c8d8f5f-269d-4e4d-85ec-c3d1b66d5bda` on `2025-09-26`; market `TPE`; stratum `T5_GE_3`.
- Comparator: `6426` / `dc37b37e-f335-4ff3-90ee-cb327cac8419` on `2025-09-26`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-2.96%`, T+10 `-4.85%`, MFE/MAE T5 `0.12%`/`-3.55%`.
- Comparator outcome: T+5 `4.86%`, T+10 `0.57%`, MFE/MAE T5 `9.29%`/`0.86%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_ONLY`; comparator `A1_ONLY`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, pullback, trend_preservation, stabilization, reclaim_turn`
- Different-looking components: `none observed`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.01228 MA20slope=0.01606; compression range20=0.1533 ratio=0.3358; volume ratio20=0.5409 contraction=True expansion=False; momentum raw5=-0.002283 RSI=55.43 MACD=-0.05394; A-state=A1_TO_A2 | trend close/MA20=0.04352 MA20slope=0.02909; compression range20=0.1486 ratio=0.4545; volume ratio20=0.9982 contraction=True expansion=False; momentum raw5=0.04225 RSI=63.03 MACD=0.2005; A-state=A1_ONLY |
| D-10 | trend close/MA20=-0.04124 MA20slope=-0.002454; compression range20=0.1086 ratio=0.6154; volume ratio20=0.8749 contraction=True expansion=False; momentum raw5=-0.04556 RSI=42.36 MACD=-0.3775; A-state=A1_TO_A2 | trend close/MA20=-0.06044 MA20slope=-0.009522; compression range20=0.1405 ratio=0.7087; volume ratio20=0.5117 contraction=True expansion=False; momentum raw5=-0.06861 RSI=39.55 MACD=-0.7871; A-state=A1_ONLY |
| D-5 | trend close/MA20=-0.01389 MA20slope=-0.0115; compression range20=0.09038 ratio=0.5065; volume ratio20=0.6934 contraction=True expansion=False; momentum raw5=0.01671 RSI=48.54 MACD=-0.1802; A-state=A1_ONLY | trend close/MA20=-0.03708 MA20slope=-0.0216; compression range20=0.1592 ratio=0.4872; volume ratio20=0.4045 contraction=True expansion=False; momentum raw5=0.002729 RSI=42.91 MACD=-0.4645; A-state=A1_ONLY |
| D-3 | trend close/MA20=-0.01822 MA20slope=-0.007144; compression range20=0.09102 ratio=0.3247; volume ratio20=0.8213 contraction=True expansion=False; momentum raw5=0.01196 RSI=46.54 MACD=-0.1431; A-state=A1_ONLY | trend close/MA20=-0.04756 MA20slope=-0.02111; compression range20=0.1625 ratio=0.4274; volume ratio20=0.6708 contraction=True expansion=False; momentum raw5=-0.008264 RSI=38.75 MACD=-0.4115; A-state=A1_ONLY |
| D-1 | trend close/MA20=0 MA20slope=-0.007166; compression range20=0.08964 ratio=0.4805; volume ratio20=1.896 contraction=False expansion=True; momentum raw5=0.002334 RSI=51.84 MACD=-0.04761; A-state=A1_ONLY | trend close/MA20=-0.04106 MA20slope=-0.02338; compression range20=0.1632 ratio=0.2735; volume ratio20=0.5107 contraction=True expansion=False; momentum raw5=-0.02846 RSI=39.62 MACD=-0.2895; A-state=A1_ONLY |
| D0 | trend close/MA20=-0.01463 MA20slope=-0.007465; compression range20=0.09112 ratio=0.5455; volume ratio20=0.8357 contraction=True expansion=False; momentum raw5=-0.008216 RSI=46.3 MACD=-0.05668; A-state=A1_ONLY | trend close/MA20=-0.0566 MA20slope=-0.02791; compression range20=0.1843 ratio=0.4109; volume ratio20=1.013 contraction=False expansion=True; momentum raw5=-0.04762 RSI=35.51 MACD=-0.3776; A-state=A1_ONLY |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 3. `B|89232205bea60e33dfce29a442c7c169ad63227a3f6dc4324517f0d80eeb84c2|T5_GE_10`

- False friend: `3535` / `4062fc71-02d5-44c2-b089-924f040f31c0` on `2026-05-19`; market `TPE`; stratum `T5_GE_10`.
- Comparator: `2449` / `e12e25cf-9eeb-424b-87bc-05c87858e95c` on `2026-05-19`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-2.65%`, T+10 `4.17%`, MFE/MAE T5 `1.14%`/`-7.95%`.
- Comparator outcome: T+5 `17.13%`, T+10 `6.06%`, MFE/MAE T5 `20.59%`/`-4.33%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `A2_WITHOUT_PRIOR_A1`; comparator `A1_ONLY`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, pullback, trend_preservation, stabilization`
- Different-looking components: `reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.04337 MA20slope=0.002942; compression range20=0.2651 ratio=0.4242; volume ratio20=1.601 contraction=False expansion=True; momentum raw5=-0.04598 RSI=53.15 MACD=0.5471; A-state=A1_ONLY | trend close/MA20=-0.03507 MA20slope=-0.01663; compression range20=0.2306 ratio=0.592; volume ratio20=1.099 contraction=False expansion=True; momentum raw5=-0.08136 RSI=44.77 MACD=-0.01088; A-state=NEITHER |
| D-10 | trend close/MA20=0.1543 MA20slope=0.05195; compression range20=0.2784 ratio=0.8025; volume ratio20=3.115 contraction=False expansion=True; momentum raw5=0.2489 RSI=66.73 MACD=2.006; A-state=A1_TO_A2 | trend close/MA20=0.2231 MA20slope=0.03672; compression range20=0.2867 ratio=0.9064; volume ratio20=1.908 contraction=False expansion=True; momentum raw5=0.2487 RSI=71.54 MACD=7.215; A-state=A1_ONLY |
| D-5 | trend close/MA20=-0.000196 MA20slope=0.0117; compression range20=0.2941 ratio=0.76; volume ratio20=0.3018 contraction=True expansion=False; momentum raw5=-0.1237 RSI=50.95 MACD=-0.263; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=0.008038 MA20slope=0.0317; compression range20=0.3173 ratio=0.7173; volume ratio20=1.082 contraction=False expansion=True; momentum raw5=-0.1497 RSI=50.4 MACD=0.8748; A-state=A1_ONLY |
| D-3 | trend close/MA20=-0.03899 MA20slope=-0.006262; compression range20=0.3074 ratio=0.3467; volume ratio20=0.2851 contraction=True expansion=False; momentum raw5=-0.07576 RSI=46.4 MACD=-1.059; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.0102 MA20slope=0.01236; compression range20=0.3226 ratio=0.4921; volume ratio20=0.9988 contraction=True expansion=False; momentum raw5=-0.1268 RSI=48.69 MACD=-1.159; A-state=A1_ONLY |
| D-1 | trend close/MA20=-0.05325 MA20slope=-0.007245; compression range20=0.3125 ratio=0.4; volume ratio20=0.2993 contraction=True expansion=False; momentum raw5=-0.04762 RSI=44.73 MACD=-1.495; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.01944 MA20slope=0.008548; compression range20=0.3237 ratio=0.2408; volume ratio20=0.7051 contraction=True expansion=False; momentum raw5=-0.01503 RSI=48.33 MACD=-2.258; A-state=A1_ONLY |
| D0 | trend close/MA20=0.03835 MA20slope=-0.003137; compression range20=0.2841 ratio=0.44; volume ratio20=1.393 contraction=False expansion=True; momentum raw5=0.03529 RSI=55.34 MACD=-0.8168; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.04225 MA20slope=0.01055; compression range20=0.3304 ratio=0.2408; volume ratio20=0.6515 contraction=True expansion=False; momentum raw5=-0.03987 RSI=46.26 MACD=-2.942; A-state=A1_ONLY |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 4. `B|4fe5da46892891e3ddff32fcacb6fbff898ed6b796d89e35b87c51dca1c5f623|T10_GE_3`

- False friend: `3346` / `090ffa57-3150-4239-ab4c-9679da611924` on `2025-02-25`; market `TPE`; stratum `T10_GE_3`.
- Comparator: `4566` / `06833556-8e76-4893-b49f-1cec4e82756f` on `2025-02-25`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.57%`, T+10 `-2.44%`, MFE/MAE T5 `1.43%`/`-3.01%`.
- Comparator outcome: T+5 `-3.44%`, T+10 `5.56%`, MFE/MAE T5 `1.59%`/`-7.14%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, pullback, trend_preservation, stabilization, reclaim_turn`
- Different-looking components: `none observed`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.04217 MA20slope=-0.02083; compression range20=0.1332 ratio=0.2644; volume ratio20=0.7407 contraction=True expansion=False; momentum raw5=-0.02683 RSI=33.48 MACD=-0.08877; A-state=NEITHER | trend close/MA20=-0.07181 MA20slope=-0.00462; compression range20=0.1944 ratio=0.2214; volume ratio20=0.2465 contraction=True expansion=False; momentum raw5=-0.04509 RSI=40.02 MACD=-0.7591; A-state=NEITHER |
| D-10 | trend close/MA20=0.05041 MA20slope=-0.005984; compression range20=0.1175 ratio=0.7927; volume ratio20=1.097 contraction=False expansion=True; momentum raw5=0.08723 RSI=59.71 MACD=0.3884; A-state=NEITHER | trend close/MA20=-0.001017 MA20slope=-0.02793; compression range20=0.209 ratio=0.3896; volume ratio20=0.6985 contraction=True expansion=False; momentum raw5=0.06196 RSI=48.19 MACD=0.2799; A-state=NEITHER |
| D-5 | trend close/MA20=0.05955 MA20slope=0.006998; compression range20=0.1213 ratio=0.2558; volume ratio20=0.3637 contraction=True expansion=False; momentum raw5=0.01576 RSI=63.45 MACD=0.4149; A-state=NEITHER | trend close/MA20=0.05867 MA20slope=-0.007726; compression range20=0.1342 ratio=0.375; volume ratio20=0.8755 contraction=True expansion=False; momentum raw5=0.05156 RSI=58.14 MACD=0.8423; A-state=NEITHER |
| D-3 | trend close/MA20=0.05201 MA20slope=0.01624; compression range20=0.1238 ratio=0.1932; volume ratio20=0.3621 contraction=True expansion=False; momentum raw5=0.01427 RSI=63.55 MACD=0.3517; A-state=NEITHER | trend close/MA20=0.04441 MA20slope=0.002929; compression range20=0.1378 ratio=0.3113; volume ratio20=0.6598 contraction=True expansion=False; momentum raw5=0.01184 RSI=55.22 MACD=0.7702; A-state=NEITHER |
| D-1 | trend close/MA20=0.03317 MA20slope=0.02121; compression range20=0.125 ratio=0.1591; volume ratio20=0.6504 contraction=True expansion=False; momentum raw5=-0.008451 RSI=58.23 MACD=0.236; A-state=NEITHER | trend close/MA20=0.03942 MA20slope=0.01341; compression range20=0.1377 ratio=0.2075; volume ratio20=0.6708 contraction=True expansion=False; momentum raw5=-0.006452 RSI=54.95 MACD=0.608; A-state=NEITHER |
| D0 | trend close/MA20=0.02099 MA20slope=0.02167; compression range20=0.1261 ratio=0.2841; volume ratio20=0.5801 contraction=True expansion=False; momentum raw5=-0.01551 RSI=53.92 MACD=0.1641; A-state=NEITHER | trend close/MA20=0.01804 MA20slope=0.01441; compression range20=0.1402 ratio=0.3113; volume ratio20=0.6245 contraction=True expansion=False; momentum raw5=-0.02452 RSI=49.91 MACD=0.4199; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 5. `B|6b21694acab1d6e3d89444e2a9e43308cdd2a15581ae389829c1ffb8e057cbb8|T10_GE_3`

- False friend: `4576` / `283240c0-a7d7-4f61-90fb-32caf79772b8` on `2025-08-15`; market `TPE`; stratum `T10_GE_3`.
- Comparator: `6531` / `5e866b70-63c6-46d1-b16c-c787bb1128b5` on `2025-08-15`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-7.87%`, T+10 `-1.97%`, MFE/MAE T5 `2.76%`/`-8.66%`.
- Comparator outcome: T+5 `-5.63%`, T+10 `5.46%`, MFE/MAE T5 `-0.17%`/`-5.97%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_TO_A2`; comparator `A1_TO_A2`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, trend_preservation, stabilization`
- Different-looking components: `pullback, reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.006885 MA20slope=-0.01211; compression range20=0.1838 ratio=0.5349; volume ratio20=2.109 contraction=False expansion=True; momentum raw5=0.02632 RSI=50.11 MACD=0.2126; A-state=NEITHER | trend close/MA20=0.06255 MA20slope=0.01576; compression range20=0.1837 ratio=0.2222; volume ratio20=0.9877 contraction=True expansion=False; momentum raw5=-0.01698 RSI=61.68 MACD=2.373; A-state=A2_WITHOUT_PRIOR_A1 |
| D-10 | trend close/MA20=-0.01582 MA20slope=-0.01258; compression range20=0.1429 ratio=0.75; volume ratio20=1.241 contraction=False expansion=True; momentum raw5=-0.03448 RSI=43.48 MACD=0.05296; A-state=NEITHER | trend close/MA20=0.134 MA20slope=0.02066; compression range20=0.2465 ratio=0.7126; volume ratio20=3.716 contraction=False expansion=True; momentum raw5=0.1405 RSI=71.11 MACD=2.037; A-state=A1_TO_A2 |
| D-5 | trend close/MA20=0.06364 MA20slope=0.007909; compression range20=0.1475 ratio=0.8611; volume ratio20=4.343 contraction=False expansion=True; momentum raw5=0.08929 RSI=59.54 MACD=0.707; A-state=A1_ONLY | trend close/MA20=-0.05173 MA20slope=0.02305; compression range20=0.2053 ratio=0.9194; volume ratio20=1.053 contraction=False expansion=True; momentum raw5=-0.1445 RSI=45.25 MACD=-1.941; A-state=A1_TO_A2 |
| D-3 | trend close/MA20=0.04581 MA20slope=0.01425; compression range20=0.1488 ratio=0.6667; volume ratio20=0.7355 contraction=True expansion=False; momentum raw5=0.04762 RSI=57.63 MACD=1.083; A-state=A1_ONLY | trend close/MA20=-0.03672 MA20slope=-0.002206; compression range20=0.2066 ratio=0.6905; volume ratio20=0.7209 contraction=True expansion=False; momentum raw5=-0.08683 RSI=46.73 MACD=-3.218; A-state=A1_TO_A2 |
| D-1 | trend close/MA20=0.06096 MA20slope=0.02253; compression range20=0.1694 ratio=0.5952; volume ratio20=0.8446 contraction=True expansion=False; momentum raw5=0.08772 RSI=60.79 MACD=1.36; A-state=A1_TO_A2 | trend close/MA20=-0.05201 MA20slope=-0.01635; compression range20=0.2114 ratio=0.2698; volume ratio20=0.6629 contraction=True expansion=False; momentum raw5=-0.04026 RSI=43.56 MACD=-3.82; A-state=A1_TO_A2 |
| D0 | trend close/MA20=0.082 MA20slope=0.02332; compression range20=0.1654 ratio=0.381; volume ratio20=1.167 contraction=False expansion=True; momentum raw5=0.04098 RSI=64.43 MACD=1.495; A-state=A1_TO_A2 | trend close/MA20=-0.06412 MA20slope=-0.01696; compression range20=0.2406 ratio=0.3262; volume ratio20=0.7762 contraction=True expansion=False; momentum raw5=-0.0298 RSI=41.33 MACD=-4.165; A-state=A1_TO_A2 |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 6. `B|5691984cac28afa6b13fbd114db4cb1ac03b4684fc824e4ae83fab501a58eb2f|T5_GE_5`

- False friend: `2634` / `2bfefa5f-1b7e-41e3-ae8e-986204c4c7e8` on `2026-01-21`; market `TPE`; stratum `T5_GE_5`.
- Comparator: `8112` / `98bc9c9c-6a01-4871-9f0f-8c964ab19e9f` on `2026-01-21`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-5.05%`, T+10 `-5.75%`, MFE/MAE T5 `1.39%`/`-5.92%`.
- Comparator outcome: T+5 `10.84%`, T+10 `1.10%`, MFE/MAE T5 `14.54%`/`0.00%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_TO_A2`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, trend_preservation, stabilization, reclaim_turn`
- Different-looking components: `pullback`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.007716 MA20slope=0.01351; compression range20=0.1978 ratio=0.2985; volume ratio20=0.3648 contraction=True expansion=False; momentum raw5=-0.009747 RSI=48.86 MACD=0.07598; A-state=NEITHER | trend close/MA20=0.02013 MA20slope=0.00497; compression range20=0.1884 ratio=0.3897; volume ratio20=0.7623 contraction=True expansion=False; momentum raw5=0.0169 RSI=53.74 MACD=-0.4093; A-state=NEITHER |
| D-10 | trend close/MA20=0.01632 MA20slope=-0.0005894; compression range20=0.09671 ratio=0.48; volume ratio20=0.732 contraction=True expansion=False; momentum raw5=0.01174 RSI=52.75 MACD=0.1755; A-state=NEITHER | trend close/MA20=0.1404 MA20slope=0.02256; compression range20=0.2166 ratio=0.6612; volume ratio20=4.06 contraction=False expansion=True; momentum raw5=0.1148 RSI=72.06 MACD=0.7799; A-state=NEITHER |
| D-5 | trend close/MA20=0.06836 MA20slope=0.01936; compression range20=0.1372 ratio=0.6316; volume ratio20=1.132 contraction=False expansion=True; momentum raw5=0.07157 RSI=63.45 MACD=0.4856; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=0.0215 MA20slope=0.01997; compression range20=0.237 ratio=0.6066; volume ratio20=0.3759 contraction=True expansion=False; momentum raw5=-0.08639 RSI=54.14 MACD=-0.06511; A-state=NEITHER |
| D-3 | trend close/MA20=0.05634 MA20slope=0.02402; compression range20=0.1372 ratio=0.6316; volume ratio20=0.8849 contraction=True expansion=False; momentum raw5=0.04331 RSI=61.98 MACD=0.4621; A-state=A1_TO_A2 | trend close/MA20=0.04221 MA20slope=0.02054; compression range20=0.2126 ratio=0.3373; volume ratio20=0.8328 contraction=True expansion=False; momentum raw5=0.01923 RSI=58.22 MACD=-0.1592; A-state=NEITHER |
| D-1 | trend close/MA20=0.08149 MA20slope=0.02759; compression range20=0.1568 ratio=0.5222; volume ratio20=2.563 contraction=False expansion=True; momentum raw5=0.04745 RSI=68.06 MACD=0.474; A-state=A1_TO_A2 | trend close/MA20=-0.009785 MA20slope=0.02511; compression range20=0.2029 ratio=0.6452; volume ratio20=1.13 contraction=False expansion=True; momentum raw5=-0.01036 RSI=50.51 MACD=-0.2211; A-state=NEITHER |
| D0 | trend close/MA20=0.07481 MA20slope=0.02989; compression range20=0.1707 ratio=0.5408; volume ratio20=1.918 contraction=False expansion=True; momentum raw5=0.0361 RSI=68.06 MACD=0.472; A-state=A1_TO_A2 | trend close/MA20=-0.05558 MA20slope=0.02137; compression range20=0.2058 ratio=0.8467; volume ratio20=0.6592 contraction=True expansion=False; momentum raw5=-0.0557 RSI=44.87 MACD=-0.6147; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 7. `B|042830e2458f3e39a83d6e27d2a5b13d93ec520767460ef3dcf59101b8b1c57f|T10_GE_10`

- False friend: `2535` / `5fc47ff1-b8c4-40f7-837f-e7cde3a7f607` on `2026-06-15`; market `TPE`; stratum `T10_GE_10`.
- Comparator: `5222` / `e70ac1dc-4720-4a78-a83e-049fdea0c5a8` on `2026-06-15`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.11%`, T+10 `-3.58%`, MFE/MAE T5 `3.79%`/`-3.26%`.
- Comparator outcome: T+5 `4.37%`, T+10 `10.48%`, MFE/MAE T5 `9.61%`/`-2.62%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": false, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`
- Same-looking components: `stabilization`
- Different-looking components: `prior_expansion, pullback, trend_preservation, reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.01042 MA20slope=0.01393; compression range20=0.1149 ratio=0.4881; volume ratio20=0.539 contraction=True expansion=False; momentum raw5=-0.01747 RSI=48.67 MACD=-0.06532; A-state=NEITHER | trend close/MA20=-0.08059 MA20slope=-0.0125; compression range20=0.2429 ratio=0.2833; volume ratio20=0.3822 contraction=True expansion=False; momentum raw5=-0.06084 RSI=38.13 MACD=-1.457; A-state=NEITHER |
| D-10 | trend close/MA20=0.0865 MA20slope=0.01601; compression range20=0.142 ratio=0.641; volume ratio20=0.7952 contraction=True expansion=False; momentum raw5=0.07432 RSI=72.1 MACD=0.6398; A-state=NEITHER | trend close/MA20=-0.01153 MA20slope=-0.01652; compression range20=0.166 ratio=0.3571; volume ratio20=0.8352 contraction=True expansion=False; momentum raw5=-0.01172 RSI=46.84 MACD=0.02635; A-state=NEITHER |
| D-5 | trend close/MA20=0.0987 MA20slope=0.02729; compression range20=0.1682 ratio=0.4722; volume ratio20=1.715 contraction=False expansion=True; momentum raw5=0.03883 RSI=73.16 MACD=0.6475; A-state=NEITHER | trend close/MA20=-0.06809 MA20slope=-0.02735; compression range20=0.1767 ratio=0.7561; volume ratio20=1.126 contraction=False expansion=True; momentum raw5=-0.083 RSI=33.02 MACD=-0.5183; A-state=NEITHER |
| D-3 | trend close/MA20=0.1292 MA20slope=0.0366; compression range20=0.2096 ratio=0.5957; volume ratio20=1.258 contraction=False expansion=True; momentum raw5=0.1101 RSI=75.69 MACD=1.111; A-state=NEITHER | trend close/MA20=-0.08261 MA20slope=-0.02859; compression range20=0.1726 ratio=0.7179; volume ratio20=0.8994 contraction=True expansion=False; momentum raw5=-0.09237 RSI=30.88 MACD=-0.9351; A-state=NEITHER |
| D-1 | trend close/MA20=0.1267 MA20slope=0.04764; compression range20=0.218 ratio=0.593; volume ratio20=0.7264 contraction=True expansion=False; momentum raw5=0.09472 RSI=77.55 MACD=1.137; A-state=NEITHER | trend close/MA20=-0.06891 MA20slope=-0.02675; compression range20=0.1762 ratio=0.4; volume ratio20=0.726 contraction=True expansion=False; momentum raw5=-0.06584 RSI=32.73 MACD=-1.011; A-state=NEITHER |
| D0 | trend close/MA20=0.1567 MA20slope=0.05417; compression range20=0.2411 ratio=0.4148; volume ratio20=1.09 contraction=False expansion=True; momentum raw5=0.1098 RSI=81.3 MACD=1.272; A-state=NEITHER | trend close/MA20=-0.05723 MA20slope=-0.0243; compression range20=0.1747 ratio=0.4; volume ratio20=0.8081 contraction=True expansion=False; momentum raw5=-0.01293 RSI=35.09 MACD=-0.8271; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 8. `B|9d91beb75f54f6354cb2f470cc1c659e7e6473142e65bc35b4577f2ab19cb512|T5_GE_5`

- False friend: `1402` / `250cb664-8122-4165-ad6c-726c488c0e2c` on `2025-08-04`; market `TPE`; stratum `T5_GE_5`.
- Comparator: `2605` / `b0819be3-9f53-4d22-88eb-14e33bb0bbcb` on `2025-08-04`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-4.31%`, T+10 `-4.14%`, MFE/MAE T5 `0.52%`/`-5.17%`.
- Comparator outcome: T+5 `7.48%`, T+10 `12.24%`, MFE/MAE T5 `9.30%`/`-0.91%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_ONLY`; comparator `A2_WITHOUT_PRIOR_A1`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`
- Comparator: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, stabilization`
- Different-looking components: `pullback, trend_preservation, reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.004896 MA20slope=0.005987; compression range20=0.05697 ratio=0.6579; volume ratio20=1.362 contraction=False expansion=True; momentum raw5=0.01368 RSI=53.11 MACD=0.06066; A-state=A1_ONLY | trend close/MA20=-0.001771 MA20slope=-0.009862; compression range20=0.08647 ratio=0.4615; volume ratio20=0.6717 contraction=True expansion=False; momentum raw5=0.03917 RSI=47.56 MACD=0.05192; A-state=NEITHER |
| D-10 | trend close/MA20=-0.09851 MA20slope=-0.0314; compression range20=0.2028 ratio=0.3675; volume ratio20=0.4987 contraction=True expansion=False; momentum raw5=-0.1082 RSI=26.86 MACD=-0.4884; A-state=A1_ONLY | trend close/MA20=0.00295 MA20slope=-0.009329; compression range20=0.09955 ratio=0.5227; volume ratio20=0.7744 contraction=True expansion=False; momentum raw5=0.02791 RSI=48.28 MACD=0.0485; A-state=NEITHER |
| D-5 | trend close/MA20=-0.06313 MA20slope=-0.03109; compression range20=0.2014 ratio=0.1026; volume ratio20=0.3649 contraction=True expansion=False; momentum raw5=0.006932 RSI=31.83 MACD=-0.1718; A-state=A1_ONLY | trend close/MA20=0.03993 MA20slope=0.0059; compression range20=0.1518 ratio=0.7; volume ratio20=1.291 contraction=False expansion=True; momentum raw5=0.04299 RSI=56.07 MACD=0.2157; A-state=A2_WITHOUT_PRIOR_A1 |
| D-3 | trend close/MA20=-0.05284 MA20slope=-0.03314; compression range20=0.2021 ratio=0.08547; volume ratio20=0.5323 contraction=True expansion=False; momentum raw5=-0.01026 RSI=32.01 MACD=-0.07884; A-state=A1_ONLY | trend close/MA20=0.02587 MA20slope=0.009768; compression range20=0.1535 ratio=0.4857; volume ratio20=0.6481 contraction=True expansion=False; momentum raw5=0.01786 RSI=53.38 MACD=0.1602; A-state=A2_WITHOUT_PRIOR_A1 |
| D-1 | trend close/MA20=-0.04176 MA20slope=-0.0367; compression range20=0.1892 ratio=0.1468; volume ratio20=0.3372 contraction=True expansion=False; momentum raw5=-0.008606 RSI=31.87 MACD=-0.01531; A-state=A1_ONLY | trend close/MA20=0.004957 MA20slope=0.004186; compression range20=0.157 ratio=0.5714; volume ratio20=0.5871 contraction=True expansion=False; momentum raw5=-0.05308 RSI=49.07 MACD=0.0669; A-state=A2_WITHOUT_PRIOR_A1 |
| D0 | trend close/MA20=-0.02807 MA20slope=-0.03773; compression range20=0.1759 ratio=0.1373; volume ratio20=0.2356 contraction=True expansion=False; momentum raw5=-0.001721 RSI=34.92 MACD=0.02961; A-state=A1_ONLY | trend close/MA20=-0.005188 MA20slope=0; compression range20=0.1587 ratio=0.5286; volume ratio20=1.134 contraction=False expansion=True; momentum raw5=-0.04338 RSI=46.93 MACD=0.02986; A-state=A2_WITHOUT_PRIOR_A1 |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 9. `B|7484c7d687127622d443dbbe734279ac1ceb610ca97851622e3d9190c94fac68|T10_GE_3`

- False friend: `2613` / `7907028c-9dd8-47fc-baa2-c1ec6a84eafe` on `2026-07-27`; market `TPE`; stratum `T10_GE_3`.
- Comparator: `1612` / `cdff5218-4d69-4ef6-b80a-eb0e277231f2` on `2026-07-27`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-4.53%`, T+10 `-2.15%`, MFE/MAE T5 `-0.24%`/`-5.49%`.
- Comparator outcome: T+5 `-2.25%`, T+10 `5.78%`, MFE/MAE T5 `0.00%`/`-6.58%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A1_ONLY`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": false, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Same-looking components: `pullback, trend_preservation, stabilization`
- Different-looking components: `prior_expansion, reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.04091 MA20slope=-0.001362; compression range20=0.09005 ratio=0.5263; volume ratio20=1.137 contraction=False expansion=True; momentum raw5=-0.03653 RSI=33.77 MACD=-0.06008; A-state=NEITHER | trend close/MA20=-0.02583 MA20slope=0.005685; compression range20=0.1727 ratio=0.3125; volume ratio20=0.5382 contraction=True expansion=False; momentum raw5=-0.03264 RSI=45.7 MACD=-0.1684; A-state=A1_TO_A2 |
| D-10 | trend close/MA20=-0.01387 MA20slope=-0.002858; compression range20=0.07907 ratio=0.7647; volume ratio20=0.7806 contraction=True expansion=False; momentum raw5=-0.03803 RSI=43.87 MACD=0.005984; A-state=A1_ONLY | trend close/MA20=-0.09989 MA20slope=-0.02723; compression range20=0.1936 ratio=0.4646; volume ratio20=1.236 contraction=False expansion=True; momentum raw5=-0.06553 RSI=22.87 MACD=-0.4902; A-state=NEITHER |
| D-5 | trend close/MA20=-0.02529 MA20slope=-0.007109; compression range20=0.08531 ratio=0.6111; volume ratio20=1.086 contraction=False expansion=True; momentum raw5=-0.0186 RSI=40.8 MACD=-0.05953; A-state=A1_ONLY | trend close/MA20=-0.1096 MA20slope=-0.04453; compression range20=0.2806 ratio=0.2874; volume ratio20=0.8948 contraction=True expansion=False; momentum raw5=-0.05488 RSI=22.94 MACD=-0.4478; A-state=NEITHER |
| D-3 | trend close/MA20=-0.02049 MA20slope=-0.006899; compression range20=0.08511 ratio=0.5278; volume ratio20=0.8928 contraction=True expansion=False; momentum raw5=-0.02982 RSI=42.06 MACD=-0.05332; A-state=A1_ONLY | trend close/MA20=-0.08107 MA20slope=-0.0466; compression range20=0.242 ratio=0.2632; volume ratio20=0.6331 contraction=True expansion=False; momentum raw5=-0.02786 RSI=27.84 MACD=-0.2803; A-state=NEITHER |
| D-1 | trend close/MA20=-0.02881 MA20slope=-0.007723; compression range20=0.09091 ratio=0.4474; volume ratio20=0.8544 contraction=True expansion=False; momentum raw5=-0.004762 RSI=38.76 MACD=-0.06126; A-state=A1_ONLY | trend close/MA20=-0.07355 MA20slope=-0.0474; compression range20=0.2351 ratio=0.226; volume ratio20=0.3715 contraction=True expansion=False; momentum raw5=0 RSI=26.37 MACD=-0.1666; A-state=NEITHER |
| D0 | trend close/MA20=-0.02615 MA20slope=-0.006236; compression range20=0.09547 ratio=0.475; volume ratio20=0.4329 contraction=True expansion=False; momentum raw5=-0.007109 RSI=39.81 MACD=-0.05721; A-state=A1_ONLY | trend close/MA20=-0.06231 MA20slope=-0.04588; compression range20=0.2311 ratio=0.1597; volume ratio20=0.3404 contraction=True expansion=False; momentum raw5=0.004839 RSI=27.62 MACD=-0.1032; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 10. `B|d38dd14487abe33a46b1b0a5521ffca7b6b87bcdae44fb8600e24fb5e8acad8c|T5_GE_3`

- False friend: `5457` / `08d6f8cf-caba-4c57-a23a-7cf3f46bed85` on `2024-11-14`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `8086` / `c123923c-cee3-4c97-91a0-9c758b714008` on `2024-11-14`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.37%`, T+10 `-2.77%`, MFE/MAE T5 `6.09%`/`-4.98%`.
- Comparator outcome: T+5 `5.07%`, T+10 `4.02%`, MFE/MAE T5 `9.94%`/`-2.22%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Same-looking components: `prior_expansion, pullback, stabilization, reclaim_turn`
- Different-looking components: `trend_preservation`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.04074 MA20slope=0.02415; compression range20=0.1128 ratio=0.5424; volume ratio20=0.7172 contraction=True expansion=False; momentum raw5=0.02953 RSI=64.01 MACD=0.278; A-state=NEITHER | trend close/MA20=-0.01718 MA20slope=0.0108; compression range20=0.1 ratio=0.7282; volume ratio20=1.49 contraction=False expansion=True; momentum raw5=-0.01435 RSI=47.91 MACD=-0.03578; A-state=NEITHER |
| D-10 | trend close/MA20=-0.0279 MA20slope=0.002995; compression range20=0.0856 ratio=0.7059; volume ratio20=0.4155 contraction=True expansion=False; momentum raw5=-0.04519 RSI=43.94 MACD=-0.2844; A-state=NEITHER | trend close/MA20=-0.0901 MA20slope=-0.028; compression range20=0.1851 ratio=0.5029; volume ratio20=0.4649 contraction=True expansion=False; momentum raw5=-0.0806 RSI=30.94 MACD=-1.172; A-state=NEITHER |
| D-5 | trend close/MA20=-0.02504 MA20slope=-0.004944; compression range20=0.1029 ratio=0.3529; volume ratio20=0.331 contraction=True expansion=False; momentum raw5=-0.002014 RSI=45.28 MACD=-0.3223; A-state=NEITHER | trend close/MA20=-0.05072 MA20slope=-0.03215; compression range20=0.2197 ratio=0.3366; volume ratio20=0.5229 contraction=True expansion=False; momentum raw5=0.00974 RSI=39.75 MACD=-0.6255; A-state=NEITHER |
| D-3 | trend close/MA20=0.1056 MA20slope=0.00485; compression range20=0.1728 ratio=0.9286; volume ratio20=12.81 contraction=False expansion=True; momentum raw5=0.1536 RSI=74.21 MACD=0.4173; A-state=NEITHER | trend close/MA20=-0.0003588 MA20slope=-0.02732; compression range20=0.2103 ratio=0.5073; volume ratio20=1.623 contraction=False expansion=True; momentum raw5=0.06209 RSI=49.51 MACD=0.03754; A-state=NEITHER |
| D-1 | trend close/MA20=0.09342 MA20slope=0.01548; compression range20=0.1735 ratio=0.9286; volume ratio20=1.46 contraction=False expansion=True; momentum raw5=0.1542 RSI=69.9 MACD=0.6631; A-state=NEITHER | trend close/MA20=0.01649 MA20slope=-0.02165; compression range20=0.1882 ratio=0.5297; volume ratio20=2.641 contraction=False expansion=True; momentum raw5=0.07197 RSI=51.27 MACD=0.5521; A-state=NEITHER |
| D0 | trend close/MA20=0.04699 MA20slope=0.01859; compression range20=0.1808 ratio=0.8163; volume ratio20=1.76 contraction=False expansion=True; momentum raw5=0.09384 RSI=58.86 MACD=0.5488; A-state=NEITHER | trend close/MA20=-0.0175 MA20slope=-0.02035; compression range20=0.1691 ratio=0.6125; volume ratio20=1.089 contraction=False expansion=True; momentum raw5=0.01393 RSI=44.57 MACD=0.4931; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 11. `B|5d5815b7d4d67f7c985cd3f44d76a07b20ec11c167390d886f8dd81960a44595|T5_GE_3`

- False friend: `2221` / `39f93559-75b3-4f65-828c-f0f27222912a` on `2026-02-03`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `6259` / `650ed659-975e-4e54-bc61-88604dc18ccc` on `2026-02-03`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.33%`, T+10 `2.65%`, MFE/MAE T5 `0.50%`/`-2.65%`.
- Comparator outcome: T+5 `7.14%`, T+10 `4.46%`, MFE/MAE T5 `11.31%`/`-0.30%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `A1_TO_A2`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, pullback, trend_preservation, stabilization`
- Different-looking components: `reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.03786 MA20slope=0.01388; compression range20=0.09683 ratio=0.3793; volume ratio20=1.489 contraction=False expansion=True; momentum raw5=0.01012 RSI=61.63 MACD=0.1115; A-state=A1_TO_A2 | trend close/MA20=0.0181 MA20slope=0.02522; compression range20=0.2333 ratio=0.5833; volume ratio20=1.384 contraction=False expansion=True; momentum raw5=-0.02703 RSI=55.77 MACD=0.005355; A-state=A1_TO_A2 |
| D-10 | trend close/MA20=0.0276 MA20slope=0.02228; compression range20=0.09194 ratio=0.2105; volume ratio20=0.6005 contraction=True expansion=False; momentum raw5=0.001616 RSI=65.36 MACD=0.03204; A-state=A1_TO_A2 | trend close/MA20=-0.01868 MA20slope=0.003076; compression range20=0.1705 ratio=0.3667; volume ratio20=0.404 contraction=True expansion=False; momentum raw5=0.02924 RSI=49.61 MACD=-0.1025; A-state=A2_WITHOUT_PRIOR_A1 |
| D-5 | trend close/MA20=0.0008995 MA20slope=0.01343; compression range20=0.08824 ratio=0.4444; volume ratio20=0.8534 contraction=True expansion=False; momentum raw5=-0.0129 RSI=54.36 MACD=-0.05923; A-state=A1_TO_A2 | trend close/MA20=-0.0005599 MA20slope=-0.004182; compression range20=0.1681 ratio=0.2; volume ratio20=0.3257 contraction=True expansion=False; momentum raw5=0.0142 RSI=52.45 MACD=-0.06142; A-state=NEITHER |
| D-3 | trend close/MA20=0.003012 MA20slope=0.0122; compression range20=0.07792 ratio=0.5; volume ratio20=0.1841 contraction=True expansion=False; momentum raw5=-0.01911 RSI=56.14 MACD=-0.08641; A-state=A1_TO_A2 | trend close/MA20=-0.03665 MA20slope=-0.009459; compression range20=0.1749 ratio=0.2667; volume ratio20=0.5704 contraction=True expansion=False; momentum raw5=-0.04722 RSI=44.03 MACD=-0.09065; A-state=NEITHER |
| D-1 | trend close/MA20=-0.02063 MA20slope=0.008518; compression range20=0.07794 ratio=0.4681; volume ratio20=1.53 contraction=False expansion=True; momentum raw5=-0.02585 RSI=47.49 MACD=-0.1472; A-state=A1_TO_A2 | trend close/MA20=-0.03792 MA20slope=-0.01244; compression range20=0.1118 ratio=0.5; volume ratio20=0.4061 contraction=True expansion=False; momentum raw5=-0.03409 RSI=42.3 MACD=-0.1195; A-state=NEITHER |
| D0 | trend close/MA20=-0.02094 MA20slope=0.007278; compression range20=0.07794 ratio=0.4681; volume ratio20=0.4711 contraction=True expansion=False; momentum raw5=-0.01471 RSI=47.49 MACD=-0.1716; A-state=A1_TO_A2 | trend close/MA20=-0.046 MA20slope=-0.014; compression range20=0.1101 ratio=0.6486; volume ratio20=0.4229 contraction=True expansion=False; momentum raw5=-0.05882 RSI=40.05 MACD=-0.1353; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 12. `B|922da6781c45a419eae6740d8e8cab67541db5624df5b249650958f1fdeab148|T5_GE_3`

- False friend: `6204` / `22ff13a6-384a-4908-bf12-cb09bc9f6560` on `2025-04-07`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `6727` / `d0f3d517-8e31-40cc-a1d7-cd592dacc01c` on `2025-04-08`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-12.19%`, T+10 `5.18%`, MFE/MAE T5 `-7.58%`/`-19.29%`.
- Comparator outcome: T+5 `9.02%`, T+10 `8.27%`, MFE/MAE T5 `9.77%`/`-9.68%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": true}`
- Comparator: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Same-looking components: `prior_expansion, pullback, stabilization`
- Different-looking components: `trend_preservation, reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=0.03802 MA20slope=0.04658; compression range20=0.2922 ratio=0.4179; volume ratio20=0.8697 contraction=True expansion=False; momentum raw5=-0.01149 RSI=57.2 MACD=0.1142; A-state=NEITHER | trend close/MA20=-0.048 MA20slope=-0.02341; compression range20=0.1414 ratio=0.3; volume ratio20=0.6485 contraction=True expansion=False; momentum raw5=-0.007022 RSI=33.3 MACD=-0.1869; A-state=NEITHER |
| D-10 | trend close/MA20=-0.02418 MA20slope=0.01175; compression range20=0.1979 ratio=0.2256; volume ratio20=0.08739 contraction=True expansion=False; momentum raw5=-0.005917 RSI=51.11 MACD=-0.4578; A-state=NEITHER | trend close/MA20=-0.009648 MA20slope=-0.02254; compression range20=0.1447 ratio=0.3168; volume ratio20=0.7065 contraction=True expansion=False; momentum raw5=0.02647 RSI=42.98 MACD=0.2583; A-state=NEITHER |
| D-5 | trend close/MA20=-0.05186 MA20slope=-0.02135; compression range20=0.1377 ratio=0.5227; volume ratio20=0.6881 contraction=True expansion=False; momentum raw5=-0.04911 RSI=42.01 MACD=-0.7434; A-state=NEITHER | trend close/MA20=-0.07085 MA20slope=-0.02575; compression range20=0.1489 ratio=0.6526; volume ratio20=2.474 contraction=False expansion=True; momentum raw5=-0.08596 RSI=27.69 MACD=-0.04493; A-state=NEITHER |
| D-3 | trend close/MA20=-0.1603 MA20slope=-0.02569; compression range20=0.3041 ratio=0.6059; volume ratio20=1.527 contraction=False expansion=True; momentum raw5=-0.1581 RSI=27.16 MACD=-1.334; A-state=NEITHER | trend close/MA20=-0.07649 MA20slope=-0.02803; compression range20=0.1869 ratio=0.5556; volume ratio20=0.2046 contraction=True expansion=False; momentum raw5=-0.06428 RSI=25.85 MACD=-0.305; A-state=NEITHER |
| D-1 | trend close/MA20=-0.1177 MA20slope=-0.03206; compression range20=0.2941 ratio=0.5412; volume ratio20=0.3536 contraction=True expansion=False; momentum raw5=-0.1053 RSI=33.39 MACD=-1.339; A-state=NEITHER | trend close/MA20=-0.1366 MA20slope=-0.03361; compression range20=0.2378 ratio=0.7445; volume ratio20=1.338 contraction=False expansion=True; momentum raw5=-0.139 RSI=22.39 MACD=-0.5515; A-state=NEITHER |
| D0 | trend close/MA20=-0.1944 MA20slope=-0.04036; compression range20=0.3743 ratio=0.5744; volume ratio20=0.2177 contraction=True expansion=False; momentum raw5=-0.1847 RSI=25.76 MACD=-1.597; A-state=NEITHER | trend close/MA20=-0.192 MA20slope=-0.04114; compression range20=0.3553 ratio=0.7196; volume ratio20=3.265 contraction=False expansion=True; momentum raw5=-0.1661 RSI=18.1 MACD=-0.9843; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 13. `B|02440b10de49d708a0ba9ac54b76932ae400b37ec9e41d83371cdfd05edb32a0|T10_GE_10`

- False friend: `4923` / `69f42d15-549a-4003-9158-d76473a649d4` on `2025-12-11`; market `TWO`; stratum `T10_GE_10`.
- Comparator: `3390` / `9c1cec41-107e-4ee4-83c4-77a055be679b` on `2025-12-11`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-0.53%`, T+10 `1.41%`, MFE/MAE T5 `5.81%`/`-2.11%`.
- Comparator outcome: T+5 `-3.79%`, T+10 `10.71%`, MFE/MAE T5 `0.45%`/`-4.69%`.
- Failure labels: `FAIL_T5_NEGATIVE`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Comparator: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, stabilization, reclaim_turn`
- Different-looking components: `pullback, trend_preservation`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.03339 MA20slope=-0.0222; compression range20=0.1917 ratio=0.4955; volume ratio20=0.5338 contraction=True expansion=False; momentum raw5=0.01579 RSI=42.29 MACD=-0.1126; A-state=NEITHER | trend close/MA20=0.00365 MA20slope=0.03396; compression range20=0.2568 ratio=0.3097; volume ratio20=0.2567 contraction=True expansion=False; momentum raw5=0.03286 RSI=56 MACD=-0.02422; A-state=A2_WITHOUT_PRIOR_A1 |
| D-10 | trend close/MA20=-0.012 MA20slope=-0.02103; compression range20=0.1373 ratio=0.2949; volume ratio20=1.181 contraction=False expansion=True; momentum raw5=-0.02069 RSI=42.93 MACD=0.08472; A-state=NEITHER | trend close/MA20=-0.001058 MA20slope=-0.01299; compression range20=0.1576 ratio=0.5522; volume ratio20=0.4078 contraction=True expansion=False; momentum raw5=0.03155 RSI=51.52 MACD=-0.05671; A-state=NEITHER |
| D-5 | trend close/MA20=-0.01493 MA20slope=-0.009393; compression range20=0.09804 ratio=0.3273; volume ratio20=0.608 contraction=True expansion=False; momentum raw5=-0.01232 RSI=41.17 MACD=0.07476; A-state=NEITHER | trend close/MA20=0.04528 MA20slope=0.009637; compression range20=0.1648 ratio=0.6486; volume ratio20=1.733 contraction=False expansion=True; momentum raw5=0.05647 RSI=61.2 MACD=0.1439; A-state=NEITHER |
| D-3 | trend close/MA20=-0.01113 MA20slope=-0.0008759; compression range20=0.07092 ratio=0.575; volume ratio20=0.2941 contraction=True expansion=False; momentum raw5=-0.007042 RSI=42.81 MACD=0.06344; A-state=NEITHER | trend close/MA20=0.06106 MA20slope=0.01115; compression range20=0.1619 ratio=0.4595; volume ratio20=1.088 contraction=False expansion=True; momentum raw5=0.04338 RSI=64.45 MACD=0.1682; A-state=NEITHER |
| D-1 | trend close/MA20=-0.005884 MA20slope=-0.001053; compression range20=0.05654 ratio=0.4375; volume ratio20=0.6465 contraction=True expansion=False; momentum raw5=-0.01565 RSI=45.01 MACD=0.05787; A-state=NEITHER | trend close/MA20=0.0408 MA20slope=0.007003; compression range20=0.1648 ratio=0.4054; volume ratio20=0.8846 contraction=True expansion=False; momentum raw5=0.002232 RSI=58.69 MACD=0.1239; A-state=NEITHER |
| D0 | trend close/MA20=-0.001406 MA20slope=-0.001229; compression range20=0.05634 ratio=0.5; volume ratio20=1.245 contraction=False expansion=True; momentum raw5=0.01248 RSI=46.17 MACD=0.0747; A-state=NEITHER | trend close/MA20=0.03752 MA20slope=0.005238; compression range20=0.1652 ratio=0.2432; volume ratio20=0.5391 contraction=True expansion=False; momentum raw5=-0.002227 RSI=57.98 MACD=0.08947; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 14. `B|392743bd1cd517f9f49902773f92a221908644498b6eefc7de1ffb44d8f520e8|T10_GE_3`

- False friend: `8109` / `a269daf5-7b59-4092-b160-d07d23fc6ee1` on `2024-11-12`; market `TWO`; stratum `T10_GE_3`.
- Comparator: `5321` / `e727774b-e52f-4ccd-987b-24c2b0c6f039` on `2024-11-12`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-1.03%`, T+10 `-0.91%`, MFE/MAE T5 `0.34%`/`-1.37%`.
- Comparator outcome: T+5 `9.14%`, T+10 `10.86%`, MFE/MAE T5 `13.79%`/`-7.76%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `NEITHER`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": false, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Comparator: `{"prior_expansion": false, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`
- Same-looking components: `prior_expansion, pullback, trend_preservation, stabilization, reclaim_turn`
- Different-looking components: `none observed`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.02641 MA20slope=-0.0001116; compression range20=0.07225 ratio=0.4603; volume ratio20=0.4644 contraction=True expansion=False; momentum raw5=-0.0257 RSI=35.66 MACD=-0.4299; A-state=NEITHER | trend close/MA20=-0.02432 MA20slope=-0.01376; compression range20=0.06406 ratio=0.5854; volume ratio20=0.6416 contraction=True expansion=False; momentum raw5=-0.01235 RSI=41.67 MACD=-0.1228; A-state=NEITHER |
| D-10 | trend close/MA20=-0.01147 MA20slope=-0.007957; compression range20=0.05943 ratio=0.25; volume ratio20=1.863 contraction=False expansion=True; momentum raw5=-0.001142 RSI=41.33 MACD=-0.04541; A-state=NEITHER | trend close/MA20=-0.05247 MA20slope=-0.02104; compression range20=0.1225 ratio=0.3919; volume ratio20=0.8895 contraction=True expansion=False; momentum raw5=-0.03668 RSI=28.09 MACD=-0.2128; A-state=NEITHER |
| D-5 | trend close/MA20=-0.0005692 MA20slope=-0.007513; compression range20=0.03986 ratio=0.8; volume ratio20=1.298 contraction=False expansion=True; momentum raw5=0.003429 RSI=45.51 MACD=0.07699; A-state=NEITHER | trend close/MA20=-0.05053 MA20slope=-0.02518; compression range20=0.1407 ratio=0.3133; volume ratio20=0.9903 contraction=True expansion=False; momentum raw5=-0.02318 RSI=26.31 MACD=-0.2099; A-state=NEITHER |
| D-3 | trend close/MA20=0.003989 MA20slope=-0.004368; compression range20=0.03973 ratio=0.8; volume ratio20=0.3118 contraction=True expansion=False; momentum raw5=0.005708 RSI=48.63 MACD=0.07436; A-state=NEITHER | trend close/MA20=-0.0331 MA20slope=-0.02213; compression range20=0.1393 ratio=0.3133; volume ratio20=0.2778 contraction=True expansion=False; momentum raw5=0.006757 RSI=32.22 MACD=-0.07908; A-state=NEITHER |
| D-1 | trend close/MA20=-0.0001139 MA20slope=-0.001422; compression range20=0.03531 ratio=0.5484; volume ratio20=0.7317 contraction=True expansion=False; momentum raw5=-0.005663 RSI=45.8 MACD=0.06707; A-state=NEITHER | trend close/MA20=-0.05199 MA20slope=-0.0217; compression range20=0.1313 ratio=0.2763; volume ratio20=2.034 contraction=False expansion=True; momentum raw5=-0.03015 RSI=25.51 MACD=-0.09631; A-state=NEITHER |
| D0 | trend close/MA20=-0.001537 MA20slope=-0.0001707; compression range20=0.03535 ratio=0.6452; volume ratio20=1.535 contraction=False expansion=True; momentum raw5=-0.001139 RSI=44.86 MACD=0.05005; A-state=NEITHER | trend close/MA20=-0.04566 MA20slope=-0.02197; compression range20=0.131 ratio=0.2763; volume ratio20=0.8353 contraction=True expansion=False; momentum raw5=-0.01695 RSI=26.52 MACD=-0.0863; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.

## 15. `B|53a3c53ebee2cc67e1594c0fbb8c48e1378030c5ebad98f919c2e1cbdfcb967c|T5_GE_3`

- False friend: `8038` / `d5e2af0a-5f1d-496d-8b50-23b9cfb50981` on `2026-07-28`; market `TWO`; stratum `T5_GE_3`.
- Comparator: `3388` / `e016b581-14f0-4681-84a2-5245ea38e8d6` on `2026-07-28`; comparator source `NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS`.
- False friend outcome: T+5 `-6.96%`, T+10 `-3.85%`, MFE/MAE T5 `0.44%`/`-10.52%`.
- Comparator outcome: T+5 `3.54%`, T+10 `2.69%`, MFE/MAE T5 `4.53%`/`-5.23%`.
- Failure labels: `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`; A-state false friend `A2_WITHOUT_PRIOR_A1`; comparator `NEITHER`.

### Component checklist

- False friend: `{"prior_expansion": false, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`
- Comparator: `{"prior_expansion": false, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`
- Same-looking components: `prior_expansion, pullback, stabilization`
- Different-looking components: `trend_preservation, reclaim_turn`

### PIT snapshots

| Day | False friend | Success comparator |
|---:|---|---|
| D-20 | trend close/MA20=-0.05439 MA20slope=-0.006329; compression range20=0.1956 ratio=0.3775; volume ratio20=0.4615 contraction=True expansion=False; momentum raw5=-0.06083 RSI=37.84 MACD=-0.1726; A-state=NEITHER | trend close/MA20=-0.1258 MA20slope=-0.04986; compression range20=0.3559 ratio=0.4083; volume ratio20=0.7198 contraction=True expansion=False; momentum raw5=-0.1193 RSI=33.5 MACD=-1.06; A-state=NEITHER |
| D-10 | trend close/MA20=-0.05801 MA20slope=0.001358; compression range20=0.2579 ratio=1; volume ratio20=1.117 contraction=False expansion=True; momentum raw5=-0.1348 RSI=42.75 MACD=0.001695; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.0867 MA20slope=-0.03568; compression range20=0.2667 ratio=0.4423; volume ratio20=1.02 contraction=False expansion=True; momentum raw5=-0.07032 RSI=34.16 MACD=-0.3068; A-state=NEITHER |
| D-5 | trend close/MA20=-0.05921 MA20slope=-0.01708; compression range20=0.2973 ratio=0.3812; volume ratio20=0.2422 contraction=True expansion=False; momentum raw5=-0.01832 RSI=41.83 MACD=-0.3538; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.1006 MA20slope=-0.04444; compression range20=0.2984 ratio=0.4429; volume ratio20=1.238 contraction=False expansion=True; momentum raw5=-0.05897 RSI=30.4 MACD=-0.4331; A-state=NEITHER |
| D-3 | trend close/MA20=-0.06853 MA20slope=-0.02076; compression range20=0.303 ratio=0.2332; volume ratio20=0.3065 contraction=True expansion=False; momentum raw5=-0.0648 RSI=39.97 MACD=-0.3795; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.08291 MA20slope=-0.04839; compression range20=0.298 ratio=0.3607; volume ratio20=1.155 contraction=False expansion=True; momentum raw5=-0.07547 RSI=31.94 MACD=-0.2602; A-state=NEITHER |
| D-1 | trend close/MA20=-0.07309 MA20slope=-0.02192; compression range20=0.3292 ratio=0.2552; volume ratio20=0.4678 contraction=True expansion=False; momentum raw5=-0.02941 RSI=38.5 MACD=-0.3502; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.06915 MA20slope=-0.04349; compression range20=0.2354 ratio=0.1561; volume ratio20=0.9777 contraction=True expansion=False; momentum raw5=0.002729 RSI=32.97 MACD=-0.02737; A-state=NEITHER |
| D0 | trend close/MA20=-0.1328 MA20slope=-0.02358; compression range20=0.3896 ratio=0.3232; volume ratio20=0.4551 contraction=True expansion=False; momentum raw5=-0.1 RSI=31.81 MACD=-0.4752; A-state=A2_WITHOUT_PRIOR_A1 | trend close/MA20=-0.09862 MA20slope=-0.0389; compression range20=0.2447 ratio=0.2601; volume ratio20=1.163 contraction=False expansion=True; momentum raw5=-0.03678 RSI=29.33 MACD=-0.1082; A-state=NEITHER |

No causal explanation is supplied. Manual review is required to determine whether visible differences are meaningful or hindsight artifacts.
