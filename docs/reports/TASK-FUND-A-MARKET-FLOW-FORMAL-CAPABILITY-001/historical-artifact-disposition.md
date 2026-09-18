# Historical artifact disposition

| Artifact | Disposition | Reason |
| --- | --- | --- |
| `docs/work-orders/FUND-001-INSTITUTION-FLOW-INITIATION-PACKET-20260913.md` | Historical provenance only | It records open discovery questions. The explicit FUND-A task prompt is the current execution authority; the packet is retained and not deleted. |
| Existing nullable `institutionFlows` references in Home/Today code | Reusable consumer boundary | The field was already a reserved consumer input, but had no formal provider/persistence path. FUND-A now supplies the additive typed shape. |
| `HomeMarketFact` aggregate/index/turnover contracts | Reusable adjacent authority | They remain the canonical market context and are not repurposed as institutional-flow facts. |
| Legacy V1/root scripts and snapshot fields | Historical provenance only / out of scope | They are not V2 formal authority and are not used to infer FUND-A values. |
| FinMind or other unverified provider paths | Missing authority | No provider substitution is introduced. |
| FUND-B/C/E workstreams and Today Signals policy | Not started | Explicitly excluded from this task. |
