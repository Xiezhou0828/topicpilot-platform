# WS3 A/B false-friend case cards

Each card is a bounded human-review candidate extracted from existing PIT-safe artifacts. The setup labels are HUMAN_DISCOVERY_HYPOTHESES only.

## Case 1 — `A_LIKE` — `4807`

- Anchor: `2024-11-12`; instrument `050ea7a6-771f-49f1-bf1f-14d617d37f84`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `4919` on `2024-11-12`.
- T+5/T+10: `-28.99%` / `-36.16%`; MFE/MAE T5 `3.37%` / `-28.99%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.1965; MA20 slope=0.05147; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.2496; compression=0.6357; vol contraction=1.042 | ratio20=1.338; contraction=False; expansion=True | raw5=0.1288; raw20=0.2664; RSI=73.1; MACD=0.4524 | NEITHER |
| D-10 | close/MA20=0.04855; MA20 slope=0.04831; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.3971; compression=0.2864; vol contraction=0.6852 | ratio20=0.5602; contraction=True; expansion=False | raw5=-0.02977; raw20=0.2648; RSI=58.97; MACD=-0.2122 | NEITHER |
| D-5 | close/MA20=0.2669; MA20 slope=0.0846; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.3499; compression=0.6929; vol contraction=0.9052 | ratio20=2.557; contraction=False; expansion=True | raw5=0.3105; raw20=0.4608; RSI=78.04; MACD=0.5661 | NEITHER |
| D-3 | close/MA20=0.1672; MA20 slope=0.08968; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.4725; compression=0.7147; vol contraction=1.161 | ratio20=0.6574; contraction=True; expansion=False | raw5=0.2063; raw20=0.332; RSI=69.77; MACD=0.5801 | NEITHER |
| D-1 | close/MA20=0.08505; MA20 slope=0.07817; MA60=0.3165 | range20=0.4216; compression=0.5776; vol contraction=1.092 | ratio20=0.3794; contraction=True; expansion=False | raw5=-0.004545; raw20=0.2882; RSI=62.19; MACD=0.2384 | NEITHER |
| D0 | close/MA20=0.1167; MA20 slope=0.06727; MA60=0.3548 | range20=0.4056; compression=0.5776; vol contraction=0.7628 | ratio20=1.026; contraction=False; expansion=True | raw5=-0.05923; raw20=0.2175; RSI=65.2; MACD=0.2032 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 2 — `A_LIKE` — `4566`

- Anchor: `2025-11-24`; instrument `06833556-8e76-4893-b49f-1cec4e82756f`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `1563` on `2025-11-24`.
- T+5/T+10: `-0.38%` / `1.53%`; MFE/MAE T5 `6.30%` / `-0.76%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.02936; MA20 slope=0.01141; MA60=-0.01628 | range20=0.1635; compression=0.3617; vol contraction=1.418 | ratio20=1.12; contraction=False; expansion=True | raw5=0.0195; raw20=0.03232; RSI=52.44; MACD=0.5368 | A1_TO_A2 |
| D-10 | close/MA20=-0.05627; MA20 slope=-0.002221; MA60=-0.08384 | range20=0.1774; compression=0.3617; vol contraction=0.8351 | ratio20=0.3969; contraction=True; expansion=False | raw5=-0.04332; raw20=-0.02752; RSI=34.97; MACD=-0.4165 | A1_TO_A2 |
| D-5 | close/MA20=-0.03538; MA20 slope=-0.01611; MA60=-0.06688 | range20=0.1839; compression=0.4286; vol contraction=0.876 | ratio20=0.9804; contraction=True; expansion=False | raw5=0.00566; raw20=-0.05496; RSI=41.66; MACD=-0.1933 | A1_TO_A2 |
| D-3 | close/MA20=-0.05155; MA20 slope=-0.02373; MA60=-0.09024 | range20=0.1896; compression=0.4286; vol contraction=1.433 | ratio20=1.509; contraction=False; expansion=True | raw5=-0.02268; raw20=-0.1296; RSI=35.97; MACD=-0.2104 | A1_ONLY |
| D-1 | close/MA20=-0.02747; MA20 slope=-0.02761; MA60=-0.07298 | range20=0.187; compression=0.3878; vol contraction=1.233 | ratio20=2.18; contraction=False; expansion=True | raw5=-0.009452; raw20=-0.1027; RSI=40.97; MACD=-0.05901 | NEITHER |
| D0 | close/MA20=-0.02284; MA20 slope=-0.0295; MA60=-0.07024 | range20=0.1393; compression=0.5205; vol contraction=1.21 | ratio20=0.4336; contraction=True; expansion=False | raw5=-0.01689; raw20=-0.0887; RSI=40.97; MACD=-0.01351 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 3 — `A_LIKE` — `3533`

- Anchor: `2024-12-13`; instrument `26fd9f8c-73bb-4aa3-abeb-1a9f0e6f5951`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6409` on `2024-12-13`.
- T+5/T+10: `-3.11%` / `0.00%`; MFE/MAE T5 `2.33%` / `-5.70%`.
- A-state: `A1_TO_A2`; failure labels `FAIL_T5_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.03576; MA20 slope=0.01051; MA60=0.05935 | range20=0.1307; compression=0.814; vol contraction=0.492 | ratio20=1.094; contraction=False; expansion=True | raw5=-0.07584; raw20=0.003049; RSI=47.2; MACD=-12.05 | NEITHER |
| D-10 | close/MA20=0.04343; MA20 slope=0.0002915; MA60=0.1292 | range20=0.1061; compression=0.9737; vol contraction=1.49 | ratio20=1.737; contraction=False; expansion=True | raw5=0.01994; raw20=0.07186; RSI=59.98; MACD=-4.834 | A1_ONLY |
| D-5 | close/MA20=0.09782; MA20 slope=0.03541; MA60=0.1947 | range20=0.2026; compression=0.4304; vol contraction=1.075 | ratio20=1.099; contraction=False; expansion=True | raw5=0.08939; raw20=0.09551; RSI=65.31; MACD=25.8 | A1_TO_A2 |
| D-3 | close/MA20=0.05307; MA20 slope=0.02741; MA60=0.1423 | range20=0.2095; compression=0.3291; vol contraction=0.5659 | ratio20=0.862; contraction=True; expansion=False | raw5=-0.04071; raw20=0.06197; RSI=58.26; MACD=13.28 | A1_TO_A2 |
| D-1 | close/MA20=0.05467; MA20 slope=0.02447; MA60=0.145 | range20=0.2068; compression=0.2658; vol contraction=0.6577 | ratio20=0.6576; contraction=True; expansion=False | raw5=-0.03778; raw20=0.1268; RSI=58.74; MACD=6.181 | A1_TO_A2 |
| D0 | close/MA20=0.05739; MA20 slope=0.02759; MA60=0.1509 | range20=0.2047; compression=0.2658; vol contraction=0.6917 | ratio20=0.5582; contraction=True; expansion=False | raw5=-0.01026; raw20=0.1733; RSI=60.16; MACD=3.535 | A1_TO_A2 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 4 — `A_LIKE` — `1597`

- Anchor: `2025-06-23`; instrument `35d31c37-7336-4a9d-8e5e-1ea4ebcc24b9`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `3588` on `2025-06-23`.
- T+5/T+10: `1.21%` / `-3.03%`; MFE/MAE T5 `8.61%` / `1.09%`.
- A-state: `NEITHER`; failure labels `FAIL_T10_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.04032; MA20 slope=0.08607; MA60=0.0436 | range20=0.3523; compression=0.2984; vol contraction=0.3897 | ratio20=0.3225; contraction=True; expansion=False | raw5=-0.01974; raw20=0.3628; RSI=57.02; MACD=0.7156 | A1_ONLY |
| D-10 | close/MA20=-0.02586; MA20 slope=0.01926; MA60=0.04886 | range20=0.1579; compression=0.5507; vol contraction=1.119 | ratio20=0.1645; contraction=True; expansion=False | raw5=0.01746; raw20=0.04048; RSI=51.14; MACD=-0.5945 | A1_ONLY |
| D-5 | close/MA20=-0.02958; MA20 slope=-0.00535; MA60=0.04735 | range20=0.1594; compression=0.4565; vol contraction=0.9579 | ratio20=0.2304; contraction=True; expansion=False | raw5=-0.009153; raw20=-0.05044; RSI=48.36; MACD=-0.5617 | A1_ONLY |
| D-3 | close/MA20=-0.03153; MA20 slope=-0.01442; MA60=0.03963 | range20=0.1167; compression=0.63; vol contraction=0.5018 | ratio20=0.2695; contraction=True; expansion=False | raw5=-0.05304; raw20=-0.0775; RSI=46.37; MACD=-0.6891 | NEITHER |
| D-1 | close/MA20=-0.05316; MA20 slope=-0.02023; MA60=0.01039 | range20=0.1386; compression=0.4348; vol contraction=0.3852 | ratio20=0.4769; contraction=True; expansion=False | raw5=-0.04598; raw20=-0.0929; RSI=40.58; MACD=-0.9081 | NEITHER |
| D0 | close/MA20=-0.05515; MA20 slope=-0.02157; MA60=0.006118 | range20=0.1697; compression=0.5357; vol contraction=0.386 | ratio20=0.2845; contraction=True; expansion=False | raw5=-0.04734; raw20=-0.07718; RSI=39.54; MACD=-0.9576 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 5 — `A_LIKE` — `9904`

- Anchor: `2025-12-09`; instrument `872f5630-9648-4f3a-8319-7958017e3e3f`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `2034` on `2025-12-09`.
- T+5/T+10: `1.46%` / `-0.97%`; MFE/MAE T5 `2.76%` / `-0.49%`.
- A-state: `A1_TO_A2`; failure labels `FAIL_T10_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.008222; MA20 slope=0.000943; MA60=0.005325 | range20=0.06908; compression=0.5; vol contraction=0.9084 | ratio20=0.4027; contraction=True; expansion=False | raw5=0.01047; raw20=-0.001724; RSI=48.34; MACD=-0.05661 | A1_TO_A2 |
| D-10 | close/MA20=0.01799; MA20 slope=-0.0004261; MA60=0.02967 | range20=0.0804; compression=0.3958; vol contraction=0.8442 | ratio20=0.6691; contraction=True; expansion=False | raw5=0.02577; raw20=0.02226; RSI=56.71; MACD=0.03319 | A1_ONLY |
| D-5 | close/MA20=0.04149; MA20 slope=0.01509; MA60=0.06225 | range20=0.09355; compression=0.4138; vol contraction=0.853 | ratio20=0.8287; contraction=True; expansion=False | raw5=0.03853; raw20=0.08202; RSI=66.62; MACD=0.1546 | A1_TO_A2 |
| D-3 | close/MA20=0.04728; MA20 slope=0.01765; MA60=0.07243 | range20=0.09236; compression=0.4483; vol contraction=0.7009 | ratio20=0.6639; contraction=True; expansion=False | raw5=0.02614; raw20=0.06803; RSI=69.93; MACD=0.1697 | A1_TO_A2 |
| D-1 | close/MA20=0.03057; MA20 slope=0.01788; MA60=0.05929 | range20=0.09164; compression=0.3333; vol contraction=0.8179 | ratio20=0.7629; contraction=True; expansion=False | raw5=0; raw20=0.07799; RSI=63.43; MACD=0.1007 | A1_TO_A2 |
| D0 | close/MA20=0.01751; MA20 slope=0.01697; MA60=0.04803 | range20=0.09091; compression=0.5; vol contraction=0.8602 | ratio20=0.8474; contraction=True; expansion=False | raw5=-0.006452; raw20=0.0639; RSI=58.45; MACD=0.05544 | A1_TO_A2 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 6 — `A_LIKE` — `3346`

- Anchor: `2026-04-22`; instrument `090ffa57-3150-4239-ab4c-9679da611924`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `3296` on `2026-04-22`.
- T+5/T+10: `-5.45%` / `-6.27%`; MFE/MAE T5 `0.82%` / `-6.54%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.05865; MA20 slope=-0.01278; MA60=-0.06843 | range20=0.1693; compression=0.7656; vol contraction=1.195 | ratio20=1.865; contraction=False; expansion=True | raw5=-0.03571; raw20=-0.08916; RSI=37.89; MACD=-0.02896 | NEITHER |
| D-10 | close/MA20=-0.04737; MA20 slope=-0.02051; MA60=-0.0992 | range20=0.1786; compression=0.2154; vol contraction=0.6923 | ratio20=1.534; contraction=False; expansion=True | raw5=-0.01887; raw20=-0.04462; RSI=36.23; MACD=-0.07596 | NEITHER |
| D-5 | close/MA20=-0.02933; MA20 slope=-0.01858; MA60=-0.0964 | range20=0.1896; compression=0.2174; vol contraction=0.3787 | ratio20=1.169; contraction=False; expansion=True | raw5=0; raw20=-0.07143; RSI=39.05; MACD=0.0119 | NEITHER |
| D-3 | close/MA20=-0.004989; MA20 slope=-0.02292; MA60=-0.08331 | range20=0.1436; compression=0.283; vol contraction=0.2151 | ratio20=0.9453; contraction=True; expansion=False | raw5=0.03073; raw20=-0.09559; RSI=43.61; MACD=0.07481 | NEITHER |
| D-1 | close/MA20=0.008975; MA20 slope=-0.02311; MA60=-0.0775 | range20=0.1132; compression=0.2619; vol contraction=0.6038 | ratio20=1.282; contraction=False; expansion=True | raw5=0.0277; raw20=-0.06784; RSI=46.37; MACD=0.1032 | NEITHER |
| D0 | close/MA20=-0.0004086; MA20 slope=-0.02093; MA60=-0.08684 | range20=0.07629; compression=0.3571; vol contraction=0.9891 | ratio20=1.267; contraction=False; expansion=True | raw5=0.008242; raw20=-0.0291; RSI=43.44; MACD=0.1037 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 7 — `A_LIKE` — `6243`

- Anchor: `2025-01-14`; instrument `1a19b207-ea85-48e1-b655-c8229410e4cb`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `2546` on `2025-01-14`.
- T+5/T+10: `-4.63%` / `3.16%`; MFE/MAE T5 `0.56%` / `-5.08%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.01726; MA20 slope=0.006849; MA60=-0.04627 | range20=0.2428; compression=0.6298; vol contraction=0.6647 | ratio20=2.626; contraction=False; expansion=True | raw5=-0.09533; raw20=0.01468; RSI=44.92; MACD=0.002273 | A2_WITHOUT_PRIOR_A1 |
| D-10 | close/MA20=-0.03221; MA20 slope=0.0007129; MA60=-0.05162 | range20=0.2376; compression=0.3274; vol contraction=0.511 | ratio20=0.2777; contraction=True; expansion=False | raw5=-0.03255; raw20=-0.02361; RSI=43.78; MACD=-0.08499 | A2_WITHOUT_PRIOR_A1 |
| D-5 | close/MA20=-0.03634; MA20 slope=-0.02; MA60=-0.06496 | range20=0.195; compression=0.2541; vol contraction=0.329 | ratio20=0.269; contraction=True; expansion=False | raw5=-0.02419; raw20=-0.1327; RSI=39.86; MACD=-0.1898 | NEITHER |
| D-3 | close/MA20=-0.02103; MA20 slope=-0.029; MA60=-0.05858 | range20=0.13; compression=0.2397; vol contraction=0.4833 | ratio20=0.6124; contraction=True; expansion=False | raw5=-0.001073; raw20=-0.09787; RSI=42.03; MACD=-0.1343 | NEITHER |
| D-1 | close/MA20=-0.07122; MA20 slope=-0.02665; MA60=-0.1094 | range20=0.179; compression=0.4395; vol contraction=1.383 | ratio20=0.56; contraction=True; expansion=False | raw5=-0.05087; raw20=-0.08455; RSI=31.19; MACD=-0.2233 | NEITHER |
| D0 | close/MA20=-0.05861; MA20 slope=-0.02378; MA60=-0.09942 | range20=0.1751; compression=0.5226; vol contraction=1.426 | ratio20=0.232; contraction=True; expansion=False | raw5=-0.04634; raw20=-0.08574; RSI=33.92; MACD=-0.2586 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 8 — `A_LIKE` — `1402`

- Anchor: `2026-03-10`; instrument `250cb664-8122-4165-ad6c-726c488c0e2c`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `2501` on `2026-03-10`.
- T+5/T+10: `-5.42%` / `-8.74%`; MFE/MAE T5 `0.87%` / `-5.59%`.
- A-state: `A1_ONLY`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.001414; MA20 slope=0.005688; MA60=0.006054 | range20=0.06018; compression=0.7059; vol contraction=1.718 | ratio20=1.176; contraction=False; expansion=True | raw5=-0.005282; raw20=0.01619; RSI=49.69; MACD=-0.01459 | A1_TO_A2 |
| D-10 | close/MA20=-0.002829; MA20 slope=-0.001148; MA60=-0.0002954 | range20=0.0727; compression=0.439; vol contraction=1.003 | ratio20=1.786; contraction=False; expansion=True | raw5=-0.01399; raw20=-0.01053; RSI=49.97; MACD=-0.005034 | A1_TO_A2 |
| D-5 | close/MA20=0.02682; MA20 slope=0.002122; MA60=0.0296 | range20=0.1512; compression=0.8182; vol contraction=0.4284 | ratio20=2.143; contraction=False; expansion=True | raw5=0.03191; raw20=0.02465; RSI=60.63; MACD=0.09979 | A1_ONLY |
| D-3 | close/MA20=-0.01387; MA20 slope=0.00115; MA60=-0.01303 | range20=0.1577; compression=0.875; vol contraction=1.148 | ratio20=1.16; contraction=False; expansion=True | raw5=-0.01933; raw20=-0.03959; RSI=44.47; MACD=-0.004528 | A1_ONLY |
| D-1 | close/MA20=0.01199; MA20 slope=0.001943; MA60=0.01458 | range20=0.1533; compression=0.4318; vol contraction=1.594 | ratio20=0.9366; contraction=True; expansion=False | raw5=-0.01544; raw20=0.01413; RSI=52.68; MACD=0.03732 | A1_ONLY |
| D0 | close/MA20=0.007841; MA20 slope=0.001323; MA60=0.01129 | range20=0.1538; compression=0.4318; vol contraction=1.592 | ratio20=0.4851; contraction=True; expansion=False | raw5=-0.01718; raw20=0.01239; RSI=51.67; MACD=0.02342 | A1_ONLY |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 9 — `A_LIKE` — `5608`

- Anchor: `2026-07-28`; instrument `74a3d5e9-22da-468a-97e3-58f744b5b73e`; market `TPE`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6168` on `2026-07-28`.
- T+5/T+10: `-0.75%` / `4.49%`; MFE/MAE T5 `0.37%` / `-4.12%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.04408; MA20 slope=-0.001181; MA60=-0.06637 | range20=0.106; compression=0.5; vol contraction=0.7931 | ratio20=0.532; contraction=True; expansion=False | raw5=-0.04392; raw20=-0.01394; RSI=37.78; MACD=-0.06638 | NEITHER |
| D-10 | close/MA20=-0.03309; MA20 slope=-0.007149; MA60=-0.05045 | range20=0.1064; compression=0.7; vol contraction=0.9894 | ratio20=1.397; contraction=False; expansion=True | raw5=-0.05686; raw20=-0.06623; RSI=40.51; MACD=-0.007095 | NEITHER |
| D-5 | close/MA20=-0.0335; MA20 slope=-0.01732; MA60=-0.05702 | range20=0.1444; compression=0.575; vol contraction=1.315 | ratio20=0.7292; contraction=True; expansion=False | raw5=-0.01773; raw20=-0.06419; RSI=41.13; MACD=-0.07544 | NEITHER |
| D-3 | close/MA20=-0.04211; MA20 slope=-0.0186; MA60=-0.06741 | range20=0.1465; compression=0.425; vol contraction=1.153 | ratio20=0.9052; contraction=True; expansion=False | raw5=-0.04545; raw20=-0.05862; RSI=38.46; MACD=-0.06778 | NEITHER |
| D-1 | close/MA20=-0.03772; MA20 slope=-0.01339; MA60=-0.06384 | range20=0.1465; compression=0.275; vol contraction=0.579 | ratio20=0.7093; contraction=True; expansion=False | raw5=0.003676; raw20=-0.03191; RSI=39.12; MACD=-0.05211 | NEITHER |
| D0 | close/MA20=-0.0562; MA20 slope=-0.01291; MA60=-0.08247 | range20=0.1573; compression=0.381; vol contraction=0.5127 | ratio20=0.8322; contraction=True; expansion=False | raw5=-0.0361; raw20=-0.05654; RSI=35.14; MACD=-0.06332 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 10 — `A_LIKE` — `6173`

- Anchor: `2024-11-12`; instrument `1ec4ef18-d868-486d-b151-cd3cbbcc55f9`; market `TWO`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6175` on `2024-11-12`.
- T+5/T+10: `-2.06%` / `0.00%`; MFE/MAE T5 `0.69%` / `-3.43%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.002716; MA20 slope=0.01328; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.1167; compression=0.3661; vol contraction=0.7279 | ratio20=0.5651; contraction=True; expansion=False | raw5=0.006289; raw20=0.07623; RSI=51.7; MACD=0.03499 | NEITHER |
| D-10 | close/MA20=-0.01031; MA20 slope=-0.0002604; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.07158; compression=0.3382; vol contraction=0.4407 | ratio20=0.9333; contraction=True; expansion=False | raw5=-0.01452; raw20=-0.02062; RSI=46.13; MACD=-0.0231 | NEITHER |
| D-5 | close/MA20=-0.05139; MA20 slope=-0.0138; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.1136; compression=0.7157; vol contraction=1.062 | ratio20=0.6302; contraction=True; expansion=False | raw5=-0.05474; raw20=-0.0587; RSI=30.31; MACD=-0.3553 | NEITHER |
| D-3 | close/MA20=-0.02823; MA20 slope=-0.01451; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.1083; compression=0.3737; vol contraction=0.7125 | ratio20=1.004; contraction=False; expansion=True | raw5=0.01218; raw20=-0.0616; RSI=39.63; MACD=-0.2643 | NEITHER |
| D-1 | close/MA20=-0.0437; MA20 slope=-0.01538; MA60=-0.05733 | range20=0.104; compression=0.3441; vol contraction=1.025 | ratio20=0.4331; contraction=True; expansion=False | raw5=-0.008869; raw20=-0.06485; RSI=33.51; MACD=-0.2319 | NEITHER |
| D0 | close/MA20=-0.06077; MA20 slope=-0.01701; MA60=-0.07702 | range20=0.1133; compression=0.4444; vol contraction=1.21 | ratio20=1.238; contraction=False; expansion=True | raw5=-0.02673; raw20=-0.08958; RSI=28.48; MACD=-0.2687 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 11 — `A_LIKE` — `3527`

- Anchor: `2026-07-21`; instrument `174b02a0-a52b-4663-a5ca-78d41bbd64f9`; market `TWO`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6530` on `2026-07-21`.
- T+5/T+10: `-11.02%` / `-12.37%`; MFE/MAE T5 `1.19%` / `-11.02%`.
- A-state: `A1_ONLY`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.1445; MA20 slope=0.04569; MA60=0.1965 | range20=0.2621; compression=0.7554; vol contraction=0.9929 | ratio20=1.607; contraction=False; expansion=True | raw5=0.1818; raw20=0.1452; RSI=67.28; MACD=1.302 | A1_TO_A2 |
| D-10 | close/MA20=0.0331; MA20 slope=0.02294; MA60=0.09757 | range20=0.2754; compression=0.3315; vol contraction=0.4381 | ratio20=1.47; contraction=False; expansion=True | raw5=0.04375; raw20=0.08972; RSI=57.48; MACD=-0.278 | A1_TO_A2 |
| D-5 | close/MA20=-0.08571; MA20 slope=0.01322; MA60=-0.02467 | range20=0.2588; compression=0.5355; vol contraction=0.748 | ratio20=0.435; contraction=True; expansion=False | raw5=-0.1033; raw20=0.008418; RSI=41.63; MACD=-0.826 | A1_TO_A2 |
| D-3 | close/MA20=-0.09098; MA20 slope=-0.004532; MA60=-0.04111 | range20=0.2632; compression=0.4129; vol contraction=0.623 | ratio20=0.2365; contraction=True; expansion=False | raw5=-0.06359; raw20=-0.1376; RSI=39.82; MACD=-0.9202 | A1_ONLY |
| D-1 | close/MA20=-0.1458; MA20 slope=-0.03474; MA60=-0.118 | range20=0.387; compression=0.4211; vol contraction=1.064 | ratio20=0.6046; contraction=True; expansion=False | raw5=-0.1248; raw20=-0.2362; RSI=31.53; MACD=-1.343 | A1_ONLY |
| D0 | close/MA20=-0.05834; MA20 slope=-0.04365; MA60=-0.03595 | range20=0.3034; compression=0.4413; vol contraction=1.576 | ratio20=1.177; contraction=False; expansion=True | raw5=-0.01503; raw20=-0.1595; RSI=44.98; MACD=-1.042 | A1_ONLY |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 12 — `A_LIKE` — `5483`

- Anchor: `2025-08-06`; instrument `76695cfa-e9cd-43a3-a929-07cf418f381a`; market `TWO`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `4760` on `2025-08-06`.
- T+5/T+10: `-1.29%` / `0.99%`; MFE/MAE T5 `8.91%` / `-2.77%`.
- A-state: `A1_TO_A2`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": true, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.02987; MA20 slope=-0.002068; MA60=-0.05722 | range20=0.1362; compression=0.4545; vol contraction=0.9837 | ratio20=0.6133; contraction=True; expansion=False | raw5=0.01893; raw20=-0.01724; RSI=49.96; MACD=0.9511 | NEITHER |
| D-10 | close/MA20=0.1002; MA20 slope=0.05306; MA60=0.06293 | range20=0.2374; compression=0.5192; vol contraction=1.456 | ratio20=0.6741; contraction=True; expansion=False | raw5=0.0961; raw20=0.1736; RSI=63.9; MACD=2.025 | A1_TO_A2 |
| D-5 | close/MA20=-0.004198; MA20 slope=0.02914; MA60=-0.006332 | range20=0.2206; compression=0.4; vol contraction=0.2352 | ratio20=0.7882; contraction=True; expansion=False | raw5=-0.06849; raw20=0.07256; RSI=49.07; MACD=-0.09104 | A1_TO_A2 |
| D-3 | close/MA20=-0.008361; MA20 slope=0.01968; MA60=-0.004473 | range20=0.2206; compression=0.4356; vol contraction=0.4206 | ratio20=0.3304; contraction=True; expansion=False | raw5=-0.05116; raw20=0.05919; RSI=49.28; MACD=-0.5742 | A1_TO_A2 |
| D-1 | close/MA20=-0.001592; MA20 slope=0.01548; MA60=0.01313 | range20=0.2068; compression=0.3178; vol contraction=0.3738 | ratio20=0.4525; contraction=True; expansion=False | raw5=0.004854; raw20=0.1022; RSI=52.41; MACD=-0.5875 | A1_TO_A2 |
| D0 | close/MA20=-0.02763; MA20 slope=0.01406; MA60=-0.009156 | range20=0.205; compression=0.3285; vol contraction=0.5228 | ratio20=0.4009; contraction=True; expansion=False | raw5=-0.009804; raw20=0.04231; RSI=47.18; MACD=-0.6904 | A1_TO_A2 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 13 — `A_LIKE` — `6290`

- Anchor: `2026-03-09`; instrument `b6624814-8ba4-4e16-a7e5-797c20612669`; market `TWO`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6274` on `2026-03-09`.
- T+5/T+10: `3.01%` / `-1.39%`; MFE/MAE T5 `5.56%` / `-6.71%`.
- A-state: `A2_WITHOUT_PRIOR_A1`; failure labels `FAIL_T10_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": true, "volume_contraction": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.01849; MA20 slope=-0.01802; MA60=-0.05017 | range20=0.1721; compression=0.3276; vol contraction=0.7945 | ratio20=0.5545; contraction=True; expansion=False | raw5=0.00597; raw20=-0.06648; RSI=45.12; MACD=-0.06622 | NEITHER |
| D-10 | close/MA20=0.09134; MA20 slope=0.01614; MA60=0.06192 | range20=0.1941; compression=0.9306; vol contraction=1.243 | ratio20=2.091; contraction=False; expansion=True | raw5=0.08798; raw20=0.1042; RSI=60.87; MACD=2.553 | A2_WITHOUT_PRIOR_A1 |
| D-5 | close/MA20=0.1771; MA20 slope=0.06457; MA60=0.1991 | range20=0.3592; compression=0.5229; vol contraction=1.193 | ratio20=1.666; contraction=False; expansion=True | raw5=0.1482; raw20=0.2716; RSI=66.3; MACD=5.626 | A2_WITHOUT_PRIOR_A1 |
| D-3 | close/MA20=0.1595; MA20 slope=0.06966; MA60=0.2031 | range20=0.3558; compression=0.4118; vol contraction=1.004 | ratio20=1.617; contraction=False; expansion=True | raw5=0.02381; raw20=0.2722; RSI=66.63; MACD=4.373 | A2_WITHOUT_PRIOR_A1 |
| D-1 | close/MA20=0.2448; MA20 slope=0.07682; MA60=0.3267 | range20=0.3674; compression=0.4886; vol contraction=1.137 | ratio20=1.566; contraction=False; expansion=True | raw5=0.05507; raw20=0.4214; RSI=74.7; MACD=5.208 | A2_WITHOUT_PRIOR_A1 |
| D0 | close/MA20=0.109; MA20 slope=0.0764; MA60=0.1919 | range20=0.4074; compression=0.4886; vol contraction=1.211 | ratio20=0.2163; contraction=True; expansion=False | raw5=0.01408; raw20=0.2819; RSI=59; MACD=3.497 | A2_WITHOUT_PRIOR_A1 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 14 — `A_LIKE` — `5328`

- Anchor: `2025-06-30`; instrument `0982ffab-8f59-44cb-850e-12edde60be38`; market `TWO`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `5302` on `2025-06-30`.
- T+5/T+10: `-1.57%` / `-0.79%`; MFE/MAE T5 `2.36%` / `-1.97%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": true, "ma_convergence_proxy": null, "participation_transition": false, "trend_background": false, "volume_contraction": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.05244; MA20 slope=0.002902; MA60=-0.06501 | range20=0.1183; compression=0.7419; vol contraction=1.001 | ratio20=0.9065; contraction=True; expansion=False | raw5=-0.05755; raw20=-0.04727; RSI=37.66; MACD=-0.07018 | NEITHER |
| D-10 | close/MA20=-0.03943; MA20 slope=-0.02086; MA60=-0.05335 | range20=0.1167; compression=0.4667; vol contraction=0.9121 | ratio20=0.7876; contraction=True; expansion=False | raw5=-0.003876; raw20=-0.09187; RSI=38.03; MACD=-0.04791 | NEITHER |
| D-5 | close/MA20=-0.06166; MA20 slope=-0.02411; MA60=-0.08039 | range20=0.1714; compression=0.5238; vol contraction=0.7908 | ratio20=1.472; contraction=False; expansion=True | raw5=-0.04669; raw20=-0.1187; RSI=28.61; MACD=-0.06839 | NEITHER |
| D-3 | close/MA20=-0.01893; MA20 slope=-0.02468; MA60=-0.04048 | range20=0.1575; compression=0.5; vol contraction=1.25 | ratio20=1.426; contraction=False; expansion=True | raw5=-0.0155; raw20=-0.07299; RSI=41.7; MACD=-0.02707 | NEITHER |
| D-1 | close/MA20=0.00563; MA20 slope=-0.01979; MA60=-0.01807 | range20=0.1158; compression=0.7333; vol contraction=0.9211 | ratio20=0.8228; contraction=True; expansion=False | raw5=0.04435; raw20=-0.05128; RSI=47.82; MACD=0.02776 | NEITHER |
| D0 | close/MA20=-0.01225; MA20 slope=-0.01513; MA60=-0.03483 | range20=0.1102; compression=0.4286; vol contraction=1.167 | ratio20=0.6332; contraction=True; expansion=False | raw5=0.03673; raw20=-0.03053; RSI=42.63; MACD=0.02641 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 15 — `A_LIKE` — `8111`

- Anchor: `2026-07-29`; instrument `6327b249-d093-4117-92f7-1e948fe54b3b`; market `TWO`.
- Setup hypothesis: `A_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `8358` on `2026-07-29`.
- T+5/T+10: `1.44%` / `-6.07%`; MFE/MAE T5 `10.22%` / `-13.26%`.
- A-state: `NEITHER`; failure labels `FAIL_T10_NEGATIVE`.
- Component checklist: `{"base_compression": true, "breakout_context_proxy": null, "improving_trend": false, "ma_convergence_proxy": null, "participation_transition": true, "trend_background": false, "volume_contraction": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.0822; MA20 slope=-0.05703; MA60=-0.1837 | range20=0.3429; compression=0.4022; vol contraction=1.16 | ratio20=0.5337; contraction=True; expansion=False | raw5=-0.05606; raw20=-0.2091; RSI=34.93; MACD=-0.2918 | NEITHER |
| D-10 | close/MA20=-0.03947; MA20 slope=-0.03248; MA60=-0.1773 | range20=0.2465; compression=0.5582; vol contraction=1.365 | ratio20=1.337; contraction=False; expansion=True | raw5=-0.01367; raw20=-0.09982; RSI=39.86; MACD=0.01903 | NEITHER |
| D-5 | close/MA20=0.01902; MA20 slope=-0.035; MA60=-0.1261 | range20=0.2592; compression=0.5672; vol contraction=1.557 | ratio20=1.803; contraction=False; expansion=True | raw5=0.02376; raw20=-0.0651; RSI=48.67; MACD=0.2416 | NEITHER |
| D-3 | close/MA20=0.1849; MA20 slope=-0.01658; MA60=0.03029 | range20=0.2954; compression=1; vol contraction=1.434 | ratio20=8.478; contraction=False; expansion=True | raw5=0.238; raw20=0.1038; RSI=62.9; MACD=1.383 | NEITHER |
| D-1 | close/MA20=0.182; MA20 slope=0.02691; MA60=0.05506 | range20=0.4029; compression=0.8052; vol contraction=0.9233 | ratio20=8.678; contraction=False; expansion=True | raw5=0.3149; raw20=0.2238; RSI=62.86; MACD=1.99 | NEITHER |
| D0 | close/MA20=0.1855; MA20 slope=0.0408; MA60=0.0707 | range20=0.3978; compression=0.6426; vol contraction=0.8644 | ratio20=3.975; contraction=False; expansion=True | raw5=0.2108; raw20=0.1992; RSI=63.88; MACD=2.027 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 16 — `B_LIKE` — `4807`

- Anchor: `2024-11-14`; instrument `050ea7a6-771f-49f1-bf1f-14d617d37f84`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `2465` on `2024-11-14`.
- T+5/T+10: `-35.44%` / `-39.22%`; MFE/MAE T5 `-9.95%` / `-36.20%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.246; MA20 slope=0.06421; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.3765; compression=0.7753; vol contraction=1.355 | ratio20=3.807; contraction=False; expansion=True | raw5=0.1641; raw20=0.34; RSI=74.52; MACD=0.7415 | NEITHER |
| D-10 | close/MA20=0.05438; MA20 slope=0.05617; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.3759; compression=0.4186; vol contraction=0.7668 | ratio20=1.327; contraction=False; expansion=True | raw5=0.0438; raw20=0.2971; RSI=61.1; MACD=-0.1212 | NEITHER |
| D-5 | close/MA20=0.1672; MA20 slope=0.08968; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.4725; compression=0.7147; vol contraction=1.161 | ratio20=0.6574; contraction=True; expansion=False | raw5=0.2063; raw20=0.332; RSI=69.77; MACD=0.5801 | NEITHER |
| D-3 | close/MA20=0.08505; MA20 slope=0.07817; MA60=0.3165 | range20=0.4216; compression=0.5776; vol contraction=1.092 | ratio20=0.3794; contraction=True; expansion=False | raw5=-0.004545; raw20=0.2882; RSI=62.19; MACD=0.2384 | NEITHER |
| D-1 | close/MA20=0.09692; MA20 slope=0.05476; MA60=0.3244 | range20=0.411; compression=0.2455; vol contraction=0.7633 | ratio20=0.6542; contraction=True; expansion=False | raw5=-0.03022; raw20=0.09238; RSI=63.32; MACD=0.1219 | NEITHER |
| D0 | close/MA20=0.07377; MA20 slope=0.04449; MA60=0.2927 | range20=0.4178; compression=0.2455; vol contraction=0.7732 | ratio20=0.8363; contraction=True; expansion=False | raw5=-0.03913; raw20=0.0995; RSI=61; MACD=0.009388 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 17 — `B_LIKE` — `2031`

- Anchor: `2025-09-26`; instrument `4c8d8f5f-269d-4e4d-85ec-c3d1b66d5bda`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6426` on `2025-09-26`.
- T+5/T+10: `-2.96%` / `-4.85%`; MFE/MAE T5 `0.12%` / `-3.55%`.
- A-state: `A1_ONLY`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.01228; MA20 slope=0.01606; MA60=0.06214 | range20=0.1533; compression=0.3358; vol contraction=0.748 | ratio20=0.5409; contraction=True; expansion=False | raw5=-0.002283; raw20=0.08842; RSI=55.43; MACD=-0.05394 | A1_TO_A2 |
| D-10 | close/MA20=-0.04124; MA20 slope=-0.002454; MA60=0.008848 | range20=0.1086; compression=0.6154; vol contraction=1.087 | ratio20=0.8749; contraction=True; expansion=False | raw5=-0.04556; raw20=-0.05418; RSI=42.36; MACD=-0.3775 | A1_TO_A2 |
| D-5 | close/MA20=-0.01389; MA20 slope=-0.0115; MA60=0.02046 | range20=0.09038; compression=0.5065; vol contraction=0.7742 | ratio20=0.6934; contraction=True; expansion=False | raw5=0.01671; raw20=-0.0274; RSI=48.54; MACD=-0.1802 | A1_ONLY |
| D-3 | close/MA20=-0.01822; MA20 slope=-0.007144; MA60=0.01089 | range20=0.09102; compression=0.3247; vol contraction=0.717 | ratio20=0.8213; contraction=True; expansion=False | raw5=0.01196; raw20=-0.0197; RSI=46.54; MACD=-0.1431 | A1_ONLY |
| D-1 | close/MA20=0; MA20 slope=-0.007166; MA60=0.02406 | range20=0.08964; compression=0.4805; vol contraction=0.5328 | ratio20=1.896; contraction=False; expansion=True | raw5=0.002334; raw20=-0.03807; RSI=51.84; MACD=-0.04761 | A1_ONLY |
| D0 | close/MA20=-0.01463; MA20 slope=-0.007465; MA60=0.006192 | range20=0.09112; compression=0.5455; vol contraction=0.7753 | ratio20=0.8357; contraction=True; expansion=False | raw5=-0.008216; raw20=-0.03318; RSI=46.3; MACD=-0.05668 | A1_ONLY |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 18 — `B_LIKE` — `3535`

- Anchor: `2026-05-19`; instrument `4062fc71-02d5-44c2-b089-924f040f31c0`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `2449` on `2026-05-19`.
- T+5/T+10: `-2.65%` / `4.17%`; MFE/MAE T5 `1.14%` / `-7.95%`.
- A-state: `A2_WITHOUT_PRIOR_A1`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.04337; MA20 slope=0.002942; MA60=0.08256 | range20=0.2651; compression=0.4242; vol contraction=0.5345 | ratio20=1.601; contraction=False; expansion=True | raw5=-0.04598; raw20=0; RSI=53.15; MACD=0.5471 | A1_ONLY |
| D-10 | close/MA20=0.1543; MA20 slope=0.05195; MA60=0.2171 | range20=0.2784; compression=0.8025; vol contraction=0.7668 | ratio20=3.115; contraction=False; expansion=True | raw5=0.2489; raw20=0.4058; RSI=66.73; MACD=2.006 | A1_TO_A2 |
| D-5 | close/MA20=-0.000196; MA20 slope=0.0117; MA60=0.04484 | range20=0.2941; compression=0.76; vol contraction=0.5622 | ratio20=0.3018; contraction=True; expansion=False | raw5=-0.1237; raw20=-0.02299; RSI=50.95; MACD=-0.263 | A2_WITHOUT_PRIOR_A1 |
| D-3 | close/MA20=-0.03899; MA20 slope=-0.006262; MA60=-0.007323 | range20=0.3074; compression=0.3467; vol contraction=0.3276 | ratio20=0.2851; contraction=True; expansion=False | raw5=-0.07576; raw20=-0.05426; RSI=46.4; MACD=-1.059 | A2_WITHOUT_PRIOR_A1 |
| D-1 | close/MA20=-0.05325; MA20 slope=-0.007245; MA60=-0.02709 | range20=0.3125; compression=0.4; vol contraction=0.3531 | ratio20=0.2993; contraction=True; expansion=False | raw5=-0.04762; raw20=-0.004149; RSI=44.73; MACD=-1.495 | A2_WITHOUT_PRIOR_A1 |
| D0 | close/MA20=0.03835; MA20 slope=-0.003137; MA60=0.06724 | range20=0.2841; compression=0.44; vol contraction=1.014 | ratio20=1.393; contraction=False; expansion=True | raw5=0.03529; raw20=0.06024; RSI=55.34; MACD=-0.8168 | A2_WITHOUT_PRIOR_A1 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 19 — `B_LIKE` — `3346`

- Anchor: `2025-02-25`; instrument `090ffa57-3150-4239-ab4c-9679da611924`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `4566` on `2025-02-25`.
- T+5/T+10: `-0.57%` / `-2.44%`; MFE/MAE T5 `1.43%` / `-3.01%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.04217; MA20 slope=-0.02083; MA60=-0.1084 | range20=0.1332; compression=0.2644; vol contraction=1.269 | ratio20=0.7407; contraction=True; expansion=False | raw5=-0.02683; raw20=-0.06313; RSI=33.48; MACD=-0.08877 | NEITHER |
| D-10 | close/MA20=0.05041; MA20 slope=-0.005984; MA60=-0.02182 | range20=0.1175; compression=0.7927; vol contraction=0.5846 | ratio20=1.097; contraction=False; expansion=True | raw5=0.08723; raw20=0.02647; RSI=59.71; MACD=0.3884 | NEITHER |
| D-5 | close/MA20=0.05955; MA20 slope=0.006998; MA60=-0.001104 | range20=0.1213; compression=0.2558; vol contraction=0.2636 | ratio20=0.3637; contraction=True; expansion=False | raw5=0.01576; raw20=0.05663; RSI=63.45; MACD=0.4149 | NEITHER |
| D-3 | close/MA20=0.05201; MA20 slope=0.01624; MA60=0.003222 | range20=0.1238; compression=0.1932; vol contraction=0.4236 | ratio20=0.3621; contraction=True; expansion=False | raw5=0.01427; raw20=0.09722; RSI=63.55; MACD=0.3517 | NEITHER |
| D-1 | close/MA20=0.03317; MA20 slope=0.02121; MA60=-0.004548 | range20=0.125; compression=0.1591; vol contraction=0.3912 | ratio20=0.6504; contraction=True; expansion=False | raw5=-0.008451; raw20=0.0781; RSI=58.23; MACD=0.236 | NEITHER |
| D0 | close/MA20=0.02099; MA20 slope=0.02167; MA60=-0.01152 | range20=0.1261; compression=0.2841; vol contraction=0.4598 | ratio20=0.5801; contraction=True; expansion=False | raw5=-0.01551; raw20=0.06891; RSI=53.92; MACD=0.1641 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 20 — `B_LIKE` — `4576`

- Anchor: `2025-08-15`; instrument `283240c0-a7d7-4f61-90fb-32caf79772b8`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6531` on `2025-08-15`.
- T+5/T+10: `-7.87%` / `-1.97%`; MFE/MAE T5 `2.76%` / `-8.66%`.
- A-state: `A1_TO_A2`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.006885; MA20 slope=-0.01211; MA60=-0.03459 | range20=0.1838; compression=0.5349; vol contraction=0.682 | ratio20=2.109; contraction=False; expansion=True | raw5=0.02632; raw20=0.0354; RSI=50.11; MACD=0.2126 | NEITHER |
| D-10 | close/MA20=-0.01582; MA20 slope=-0.01258; MA60=-0.07983 | range20=0.1429; compression=0.75; vol contraction=0.4999 | ratio20=1.241; contraction=False; expansion=True | raw5=-0.03448; raw20=-0.05085; RSI=43.48; MACD=0.05296 | NEITHER |
| D-5 | close/MA20=0.06364; MA20 slope=0.007909; MA60=0.01287 | range20=0.1475; compression=0.8611; vol contraction=1.195 | ratio20=4.343; contraction=False; expansion=True | raw5=0.08929; raw20=0.07018; RSI=59.54; MACD=0.707 | A1_ONLY |
| D-3 | close/MA20=0.04581; MA20 slope=0.01425; MA60=0.009034 | range20=0.1488; compression=0.6667; vol contraction=1.311 | ratio20=0.7355; contraction=True; expansion=False | raw5=0.04762; raw20=0.08036; RSI=57.63; MACD=1.083 | A1_ONLY |
| D-1 | close/MA20=0.06096; MA20 slope=0.02253; MA60=0.0373 | range20=0.1694; compression=0.5952; vol contraction=1.225 | ratio20=0.8446; contraction=True; expansion=False | raw5=0.08772; raw20=0.08772; RSI=60.79; MACD=1.36 | A1_TO_A2 |
| D0 | close/MA20=0.082; MA20 slope=0.02332; MA60=0.0638 | range20=0.1654; compression=0.381; vol contraction=0.6932 | ratio20=1.167; contraction=False; expansion=True | raw5=0.04098; raw20=0.08547; RSI=64.43; MACD=1.495 | A1_TO_A2 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 21 — `B_LIKE` — `2634`

- Anchor: `2026-01-21`; instrument `2bfefa5f-1b7e-41e3-ae8e-986204c4c7e8`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `8112` on `2026-01-21`.
- T+5/T+10: `-5.05%` / `-5.75%`; MFE/MAE T5 `1.39%` / `-5.92%`.
- A-state: `A1_TO_A2`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.007716; MA20 slope=0.01351; MA60=-0.03997 | range20=0.1978; compression=0.2985; vol contraction=0.5213 | ratio20=0.3648; contraction=True; expansion=False | raw5=-0.009747; raw20=0.05285; RSI=48.86; MACD=0.07598 | NEITHER |
| D-10 | close/MA20=0.01632; MA20 slope=-0.0005894; MA60=-0.003982 | range20=0.09671; compression=0.48; vol contraction=0.6836 | ratio20=0.732; contraction=True; expansion=False | raw5=0.01174; raw20=0.005837; RSI=52.75; MACD=0.1755 | NEITHER |
| D-5 | close/MA20=0.06836; MA20 slope=0.01936; MA60=0.07057 | range20=0.1372; compression=0.6316; vol contraction=1.499 | ratio20=1.132; contraction=False; expansion=True | raw5=0.07157; raw20=0.07992; RSI=63.45; MACD=0.4856 | A2_WITHOUT_PRIOR_A1 |
| D-3 | close/MA20=0.05634; MA20 slope=0.02402; MA60=0.07053 | range20=0.1372; compression=0.6316; vol contraction=0.6408 | ratio20=0.8849; contraction=True; expansion=False | raw5=0.04331; raw20=0.1192; RSI=61.98; MACD=0.4621 | A1_TO_A2 |
| D-1 | close/MA20=0.08149; MA20 slope=0.02759; MA60=0.1086 | range20=0.1568; compression=0.5222; vol contraction=0.6247 | ratio20=2.563; contraction=False; expansion=True | raw5=0.04745; raw20=0.1299; RSI=68.06; MACD=0.474 | A1_TO_A2 |
| D0 | close/MA20=0.07481; MA20 slope=0.02989; MA60=0.1078 | range20=0.1707; compression=0.5408; vol contraction=0.6488 | ratio20=1.918; contraction=False; expansion=True | raw5=0.0361; raw20=0.1299; RSI=68.06; MACD=0.472 | A1_TO_A2 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 22 — `B_LIKE` — `2535`

- Anchor: `2026-06-15`; instrument `5fc47ff1-b8c4-40f7-837f-e7cde3a7f607`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `5222` on `2026-06-15`.
- T+5/T+10: `-0.11%` / `-3.58%`; MFE/MAE T5 `3.79%` / `-3.26%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": false, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.01042; MA20 slope=0.01393; MA60=0.008299 | range20=0.1149; compression=0.4881; vol contraction=0.5027 | ratio20=0.539; contraction=True; expansion=False | raw5=-0.01747; raw20=0.04131; RSI=48.67; MACD=-0.06532 | NEITHER |
| D-10 | close/MA20=0.0865; MA20 slope=0.01601; MA60=0.1232 | range20=0.142; compression=0.641; vol contraction=0.9611 | ratio20=0.7952; contraction=True; expansion=False | raw5=0.07432; raw20=0.1241; RSI=72.1; MACD=0.6398 | NEITHER |
| D-5 | close/MA20=0.0987; MA20 slope=0.02729; MA60=0.1526 | range20=0.1682; compression=0.4722; vol contraction=1.263 | ratio20=1.715; contraction=False; expansion=True | raw5=0.03883; raw20=0.1505; RSI=73.16; MACD=0.6475 | NEITHER |
| D-3 | close/MA20=0.1292; MA20 slope=0.0366; MA60=0.1984 | range20=0.2096; compression=0.5957; vol contraction=1.312 | ratio20=1.258; contraction=False; expansion=True | raw5=0.1101; raw20=0.196; RSI=75.69; MACD=1.111 | NEITHER |
| D-1 | close/MA20=0.1267; MA20 slope=0.04764; MA60=0.2101 | range20=0.218; compression=0.593; vol contraction=1.155 | ratio20=0.7264; contraction=True; expansion=False | raw5=0.09472; raw20=0.2157; RSI=77.55; MACD=1.137 | NEITHER |
| D0 | close/MA20=0.1567; MA20 slope=0.05417; MA60=0.2531 | range20=0.2411; compression=0.4148; vol contraction=1.28 | ratio20=1.09; contraction=False; expansion=True | raw5=0.1098; raw20=0.2996; RSI=81.3; MACD=1.272 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 23 — `B_LIKE` — `1402`

- Anchor: `2025-08-04`; instrument `250cb664-8122-4165-ad6c-726c488c0e2c`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `2605` on `2025-08-04`.
- T+5/T+10: `-4.31%` / `-4.14%`; MFE/MAE T5 `0.52%` / `-5.17%`.
- A-state: `A1_ONLY`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.004896; MA20 slope=0.005987; MA60=0.01268 | range20=0.05697; compression=0.6579; vol contraction=1.195 | ratio20=1.362; contraction=False; expansion=True | raw5=0.01368; raw20=0.01832; RSI=53.11; MACD=0.06066 | A1_ONLY |
| D-10 | close/MA20=-0.09851; MA20 slope=-0.0314; MA60=-0.1176 | range20=0.2028; compression=0.3675; vol contraction=1.632 | ratio20=0.4987; contraction=True; expansion=False | raw5=-0.1082; raw20=-0.115; RSI=26.86; MACD=-0.4884 | A1_ONLY |
| D-5 | close/MA20=-0.06313; MA20 slope=-0.03109; MA60=-0.103 | range20=0.2014; compression=0.1026; vol contraction=0.3957 | ratio20=0.3649; contraction=True; expansion=False | raw5=0.006932; raw20=-0.117; RSI=31.83; MACD=-0.1718 | A1_ONLY |
| D-3 | close/MA20=-0.05284; MA20 slope=-0.03314; MA60=-0.1003 | range20=0.2021; compression=0.08547; vol contraction=0.2003 | ratio20=0.5323; contraction=True; expansion=False | raw5=-0.01026; raw20=-0.1345; RSI=32.01; MACD=-0.07884 | A1_ONLY |
| D-1 | close/MA20=-0.04176; MA20 slope=-0.0367; MA60=-0.09972 | range20=0.1892; compression=0.1468; vol contraction=0.2178 | ratio20=0.3372; contraction=True; expansion=False | raw5=-0.008606; raw20=-0.1479; RSI=31.87; MACD=-0.01531 | A1_ONLY |
| D0 | close/MA20=-0.02807; MA20 slope=-0.03773; MA60=-0.09089 | range20=0.1759; compression=0.1373; vol contraction=0.2626 | ratio20=0.2356; contraction=True; expansion=False | raw5=-0.001721; raw20=-0.1304; RSI=34.92; MACD=0.02961 | A1_ONLY |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 24 — `B_LIKE` — `2613`

- Anchor: `2026-07-27`; instrument `7907028c-9dd8-47fc-baa2-c1ec6a84eafe`; market `TPE`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `1612` on `2026-07-27`.
- T+5/T+10: `-4.53%` / `-2.15%`; MFE/MAE T5 `-0.24%` / `-5.49%`.
- A-state: `A1_ONLY`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": false, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.04091; MA20 slope=-0.001362; MA60=-0.05409 | range20=0.09005; compression=0.5263; vol contraction=0.5521 | ratio20=1.137; contraction=False; expansion=True | raw5=-0.03653; raw20=-0.00939; RSI=33.77; MACD=-0.06008 | NEITHER |
| D-10 | close/MA20=-0.01387; MA20 slope=-0.002858; MA60=-0.02619 | range20=0.07907; compression=0.7647; vol contraction=0.7636 | ratio20=0.7806; contraction=True; expansion=False | raw5=-0.03803; raw20=-0.0205; RSI=43.87; MACD=0.005984 | A1_ONLY |
| D-5 | close/MA20=-0.02529; MA20 slope=-0.007109; MA60=-0.03832 | range20=0.08531; compression=0.6111; vol contraction=1.11 | ratio20=1.086; contraction=False; expansion=True | raw5=-0.0186; raw20=-0.03653; RSI=40.8; MACD=-0.05953 | A1_ONLY |
| D-3 | close/MA20=-0.02049; MA20 slope=-0.006899; MA60=-0.03406 | range20=0.08511; compression=0.5278; vol contraction=0.8311 | ratio20=0.8928; contraction=True; expansion=False | raw5=-0.02982; raw20=-0.02759; RSI=42.06; MACD=-0.05332 | A1_ONLY |
| D-1 | close/MA20=-0.02881; MA20 slope=-0.007723; MA60=-0.04341 | range20=0.09091; compression=0.4474; vol contraction=0.4096 | ratio20=0.8544; contraction=True; expansion=False | raw5=-0.004762; raw20=-0.03016; RSI=38.76; MACD=-0.06126 | A1_ONLY |
| D0 | close/MA20=-0.02615; MA20 slope=-0.006236; MA60=-0.03998 | range20=0.09547; compression=0.475; vol contraction=0.4011 | ratio20=0.4329; contraction=True; expansion=False | raw5=-0.007109; raw20=-0.007109; RSI=39.81; MACD=-0.05721 | A1_ONLY |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 25 — `B_LIKE` — `5457`

- Anchor: `2024-11-14`; instrument `08d6f8cf-caba-4c57-a23a-7cf3f46bed85`; market `TWO`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `8086` on `2024-11-14`.
- T+5/T+10: `-0.37%` / `-2.77%`; MFE/MAE T5 `6.09%` / `-4.98%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.04074; MA20 slope=0.02415; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.1128; compression=0.5424; vol contraction=0.989 | ratio20=0.7172; contraction=True; expansion=False | raw5=0.02953; raw20=0.1034; RSI=64.01; MACD=0.278 | NEITHER |
| D-10 | close/MA20=-0.0279; MA20 slope=0.002995; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.0856; compression=0.7059; vol contraction=0.6516 | ratio20=0.4155; contraction=True; expansion=False | raw5=-0.04519; raw20=-0.01096; RSI=43.94; MACD=-0.2844 | NEITHER |
| D-5 | close/MA20=-0.02504; MA20 slope=-0.004944; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.1029; compression=0.3529; vol contraction=0.501 | ratio20=0.331; contraction=True; expansion=False | raw5=-0.002014; raw20=-0.02461; RSI=45.28; MACD=-0.3223 | NEITHER |
| D-3 | close/MA20=0.1056; MA20 slope=0.00485; MA60=0.1378 | range20=0.1728; compression=0.9286; vol contraction=1.472 | ratio20=12.81; contraction=False; expansion=True | raw5=0.1536; raw20=0.09249; RSI=74.21; MACD=0.4173 | NEITHER |
| D-1 | close/MA20=0.09342; MA20 slope=0.01548; MA60=0.1284 | range20=0.1735; compression=0.9286; vol contraction=1.494 | ratio20=1.46; contraction=False; expansion=True | raw5=0.1542; raw20=0.08238; RSI=69.9; MACD=0.6631 | NEITHER |
| D0 | close/MA20=0.04699; MA20 slope=0.01859; MA60=0.08054 | range20=0.1808; compression=0.8163; vol contraction=1.724 | ratio20=1.76; contraction=False; expansion=True | raw5=0.09384; raw20=0.03633; RSI=58.86; MACD=0.5488 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 26 — `B_LIKE` — `2221`

- Anchor: `2026-02-03`; instrument `39f93559-75b3-4f65-828c-f0f27222912a`; market `TWO`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6259` on `2026-02-03`.
- T+5/T+10: `-0.33%` / `2.65%`; MFE/MAE T5 `0.50%` / `-2.65%`.
- A-state: `A1_TO_A2`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.03786; MA20 slope=0.01388; MA60=0.05085 | range20=0.09683; compression=0.3793; vol contraction=1.154 | ratio20=1.489; contraction=False; expansion=True | raw5=0.01012; raw20=0.06774; RSI=61.63; MACD=0.1115 | A1_TO_A2 |
| D-10 | close/MA20=0.0276; MA20 slope=0.02228; MA60=0.07254 | range20=0.09194; compression=0.2105; vol contraction=0.2473 | ratio20=0.6005; contraction=True; expansion=False | raw5=0.001616; raw20=0.09155; RSI=65.36; MACD=0.03204 | A1_TO_A2 |
| D-5 | close/MA20=0.0008995; MA20 slope=0.01343; MA60=0.05094 | range20=0.08824; compression=0.4444; vol contraction=0.9875 | ratio20=0.8534; contraction=True; expansion=False | raw5=-0.0129; raw20=0.03204; RSI=54.36; MACD=-0.05923 | A1_TO_A2 |
| D-3 | close/MA20=0.003012; MA20 slope=0.0122; MA60=0.05516 | range20=0.07792; compression=0.5; vol contraction=0.6793 | ratio20=0.1841; contraction=True; expansion=False | raw5=-0.01911; raw20=0.02667; RSI=56.14; MACD=-0.08641 | A1_TO_A2 |
| D-1 | close/MA20=-0.02063; MA20 slope=0.008518; MA60=0.03083 | range20=0.07794; compression=0.4681; vol contraction=0.7316 | ratio20=1.53; contraction=False; expansion=True | raw5=-0.02585; raw20=0.02551; RSI=47.49; MACD=-0.1472 | A1_TO_A2 |
| D0 | close/MA20=-0.02094; MA20 slope=0.007278; MA60=0.02992 | range20=0.07794; compression=0.4681; vol contraction=0.7374 | ratio20=0.4711; contraction=True; expansion=False | raw5=-0.01471; raw20=0.006678; RSI=47.49; MACD=-0.1716 | A1_TO_A2 |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 27 — `B_LIKE` — `6204`

- Anchor: `2025-04-07`; instrument `22ff13a6-384a-4908-bf12-cb09bc9f6560`; market `TWO`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `6727` on `2025-04-08`.
- T+5/T+10: `-12.19%` / `5.18%`; MFE/MAE T5 `-7.58%` / `-19.29%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": true}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=0.03802; MA20 slope=0.04658; MA60=0.08035 | range20=0.2922; compression=0.4179; vol contraction=0.816 | ratio20=0.8697; contraction=True; expansion=False | raw5=-0.01149; raw20=0.222; RSI=57.2; MACD=0.1142 | NEITHER |
| D-10 | close/MA20=-0.02418; MA20 slope=0.01175; MA60=0.06802 | range20=0.1979; compression=0.2256; vol contraction=0.3038 | ratio20=0.08739; contraction=True; expansion=False | raw5=-0.005917; raw20=0.04673; RSI=51.11; MACD=-0.4578 | NEITHER |
| D-5 | close/MA20=-0.05186; MA20 slope=-0.02135; MA60=0.01423 | range20=0.1377; compression=0.5227; vol contraction=0.8524 | ratio20=0.6881; contraction=True; expansion=False | raw5=-0.04911; raw20=-0.0819; RSI=42.01; MACD=-0.7434 | NEITHER |
| D-3 | close/MA20=-0.1603; MA20 slope=-0.02569; MA60=-0.1113 | range20=0.3041; compression=0.6059; vol contraction=1.133 | ratio20=1.527; contraction=False; expansion=True | raw5=-0.1581; raw20=-0.1426; RSI=27.16; MACD=-1.334 | NEITHER |
| D-1 | close/MA20=-0.1177; MA20 slope=-0.03206; MA60=-0.07945 | range20=0.2941; compression=0.5412; vol contraction=1.592 | ratio20=0.3536; contraction=True; expansion=False | raw5=-0.1053; raw20=-0.1731; RSI=33.39; MACD=-1.339 | NEITHER |
| D0 | close/MA20=-0.1944; MA20 slope=-0.04036; MA60=-0.1682 | range20=0.3743; compression=0.5744; vol contraction=1.56 | ratio20=0.2177; contraction=True; expansion=False | raw5=-0.1847; raw20=-0.2427; RSI=25.76; MACD=-1.597 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 28 — `B_LIKE` — `4923`

- Anchor: `2025-12-11`; instrument `69f42d15-549a-4003-9158-d76473a649d4`; market `TWO`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `3390` on `2025-12-11`.
- T+5/T+10: `-0.53%` / `1.41%`; MFE/MAE T5 `5.81%` / `-2.11%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE`.
- Component checklist: `{"prior_expansion": true, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.03339; MA20 slope=-0.0222; MA60=-0.06321 | range20=0.1917; compression=0.4955; vol contraction=0.8909 | ratio20=0.5338; contraction=True; expansion=False | raw5=0.01579; raw20=-0.0477; RSI=42.29; MACD=-0.1126 | NEITHER |
| D-10 | close/MA20=-0.012; MA20 slope=-0.02103; MA60=-0.07235 | range20=0.1373; compression=0.2949; vol contraction=0.9574 | ratio20=1.181; contraction=False; expansion=True | raw5=-0.02069; raw20=-0.04377; RSI=42.93; MACD=0.08472 | NEITHER |
| D-5 | close/MA20=-0.01493; MA20 slope=-0.009393; MA60=-0.07766 | range20=0.09804; compression=0.3273; vol contraction=0.778 | ratio20=0.608; contraction=True; expansion=False | raw5=-0.01232; raw20=-0.01579; RSI=41.17; MACD=0.07476 | NEITHER |
| D-3 | close/MA20=-0.01113; MA20 slope=-0.0008759; MA60=-0.06938 | range20=0.07092; compression=0.575; vol contraction=0.8546 | ratio20=0.2941; contraction=True; expansion=False | raw5=-0.007042; raw20=0.01439; RSI=42.81; MACD=0.06344 | NEITHER |
| D-1 | close/MA20=-0.005884; MA20 slope=-0.001053; MA60=-0.0617 | range20=0.05654; compression=0.4375; vol contraction=0.9331 | ratio20=0.6465; contraction=True; expansion=False | raw5=-0.01565; raw20=-0.02414; RSI=45.01; MACD=0.05787 | NEITHER |
| D0 | close/MA20=-0.001406; MA20 slope=-0.001229; MA60=-0.05653 | range20=0.05634; compression=0.5; vol contraction=0.5642 | ratio20=1.245; contraction=False; expansion=True | raw5=0.01248; raw20=-0.019; RSI=46.17; MACD=0.0747 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 29 — `B_LIKE` — `8109`

- Anchor: `2024-11-12`; instrument `a269daf5-7b59-4092-b160-d07d23fc6ee1`; market `TWO`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `5321` on `2024-11-12`.
- T+5/T+10: `-1.03%` / `-0.91%`; MFE/MAE T5 `0.34%` / `-1.37%`.
- A-state: `NEITHER`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": false, "pullback": true, "reclaim_turn": true, "stabilization": true, "trend_preservation": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.02641; MA20 slope=-0.0001116; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.07225; compression=0.4603; vol contraction=0.6963 | ratio20=0.4644; contraction=True; expansion=False | raw5=-0.0257; raw20=-0.004566; RSI=35.66; MACD=-0.4299 | NEITHER |
| D-10 | close/MA20=-0.01147; MA20 slope=-0.007957; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.05943; compression=0.25; vol contraction=0.6863 | ratio20=1.863; contraction=False; expansion=True | raw5=-0.001142; raw20=-0.04372; RSI=41.33; MACD=-0.04541 | NEITHER |
| D-5 | close/MA20=-0.0005692; MA20 slope=-0.007513; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.03986; compression=0.8; vol contraction=1.063 | ratio20=1.298; contraction=False; expansion=True | raw5=0.003429; raw20=-0.01899; RSI=45.51; MACD=0.07699 | NEITHER |
| D-3 | close/MA20=0.003989; MA20 slope=-0.004368; MA60=NOT_AVAILABLE_FROM_EXISTING_ARTIFACTS | range20=0.03973; compression=0.8; vol contraction=1.142 | ratio20=0.3118; contraction=True; expansion=False | raw5=0.005708; raw20=-0.003394; RSI=48.63; MACD=0.07436 | NEITHER |
| D-1 | close/MA20=-0.0001139; MA20 slope=-0.001422; MA60=-0.01039 | range20=0.03531; compression=0.5484; vol contraction=0.7385 | ratio20=0.7317; contraction=True; expansion=False | raw5=-0.005663; raw20=0.01036; RSI=45.8; MACD=0.06707 | NEITHER |
| D0 | close/MA20=-0.001537; MA20 slope=-0.0001707; MA60=-0.01127 | range20=0.03535; compression=0.6452; vol contraction=0.5693 | ratio20=1.535; contraction=False; expansion=True | raw5=-0.001139; raw20=0.005734; RSI=44.86; MACD=0.05005 | NEITHER |

Owner review boundary: do not infer why this case failed from this card alone.

## Case 30 — `B_LIKE` — `8038`

- Anchor: `2026-07-28`; instrument `d5e2af0a-5f1d-496d-8b50-23b9cfb50981`; market `TWO`.
- Setup hypothesis: `B_LIKE`; status `FAILURE_CANDIDATE`.
- Comparator: `3388` on `2026-07-28`.
- T+5/T+10: `-6.96%` / `-3.85%`; MFE/MAE T5 `0.44%` / `-10.52%`.
- A-state: `A2_WITHOUT_PRIOR_A1`; failure labels `FAIL_T5_NEGATIVE,FAIL_T10_NEGATIVE,FAIL_NO_EXPANSION`.
- Component checklist: `{"prior_expansion": false, "pullback": true, "reclaim_turn": false, "stabilization": true, "trend_preservation": false}`

| Day | Trend | Compression | Volume | Momentum | A-state |
|---:|---|---|---|---|---|
| D-20 | close/MA20=-0.05439; MA20 slope=-0.006329; MA60=-0.07393 | range20=0.1956; compression=0.3775; vol contraction=0.8033 | ratio20=0.4615; contraction=True; expansion=False | raw5=-0.06083; raw20=-0.05854; RSI=37.84; MACD=-0.1726 | NEITHER |
| D-10 | close/MA20=-0.05801; MA20 slope=0.001358; MA60=-0.08576 | range20=0.2579; compression=1; vol contraction=1.448 | ratio20=1.117; contraction=False; expansion=True | raw5=-0.1348; raw20=-0.07729; RSI=42.75; MACD=0.001695 | A2_WITHOUT_PRIOR_A1 |
| D-5 | close/MA20=-0.05921; MA20 slope=-0.01708; MA60=-0.08863 | range20=0.2973; compression=0.3812; vol contraction=0.5338 | ratio20=0.2422; contraction=True; expansion=False | raw5=-0.01832; raw20=-0.08759; RSI=41.83; MACD=-0.3538 | A2_WITHOUT_PRIOR_A1 |
| D-3 | close/MA20=-0.06853; MA20 slope=-0.02076; MA60=-0.1007 | range20=0.303; compression=0.2332; vol contraction=0.4274 | ratio20=0.3065; contraction=True; expansion=False | raw5=-0.0648; raw20=-0.09023; RSI=39.97; MACD=-0.3795 | A2_WITHOUT_PRIOR_A1 |
| D-1 | close/MA20=-0.07309; MA20 slope=-0.02192; MA60=-0.1085 | range20=0.3292; compression=0.2552; vol contraction=0.1755 | ratio20=0.4678; contraction=True; expansion=False | raw5=-0.02941; raw20=-0.06923; RSI=38.5; MACD=-0.3502 | A2_WITHOUT_PRIOR_A1 |
| D0 | close/MA20=-0.1328; MA20 slope=-0.02358; MA60=-0.1682 | range20=0.3896; compression=0.3232; vol contraction=0.5708 | ratio20=0.4551; contraction=True; expansion=False | raw5=-0.1; raw20=-0.1256; RSI=31.81; MACD=-0.4752 | A2_WITHOUT_PRIOR_A1 |

Owner review boundary: do not infer why this case failed from this card alone.
