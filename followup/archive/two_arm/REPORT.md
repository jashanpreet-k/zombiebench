# Follow-up review

## The 18 new Experiment 2 cases

| Case ID | Domain | Mistake | Faulty route | Gold |
|---|---|---|---|---|
| zf2-01-different | Cold-chain dispatch | Timezone | `WarehouseScanner.service_day` | new |
| zf2-01-same | Cold-chain dispatch | Timezone | `DispatchManifest.service_day` | regression #5111 |
| zf2-02-different | Water utility billing | Rounding | `AdjustmentBatch.total` | new |
| zf2-02-same | Water utility billing | Rounding | `BillComposer.total` | regression #5211 |
| zf2-03-different | Library circulation | Cache | `ReservationSlip.load` | new |
| zf2-03-same | Library circulation | Cache | `CatalogCard.load` | regression #5311 |
| zf2-04-different | Pathology administration | Null reference | `CourierManifest.contact` | new |
| zf2-04-same | Pathology administration | Null reference | `SpecimenLabel.contact` | regression #5411 |
| zf2-05-different | EV charging reservations | Race condition | `FleetReservation.claim` | new |
| zf2-05-same | EV charging reservations | Race condition | `AppReservation.claim` | regression #5511 |
| zf2-06-different | Drone survey planning | Unit conversion | `BulkRouteImport.height` | new |
| zf2-06-same | Drone survey planning | Unit conversion | `WaypointEditor.height` | regression #5611 |
| zf2-07-different | Satellite ground operations | Timezone | `HandoverPacket.day` | new |
| zf2-07-same | Satellite ground operations | Timezone | `StationCalendar.day` | regression #5711 |
| zf2-08-different | Energy settlement | Rounding | `PartnerSettlement.amount` | new |
| zf2-08-same | Energy settlement | Rounding | `RetailSettlement.amount` | regression #5811 |
| zf2-09-different | Transit service alerts | Cache | `DriverBriefing.notice` | new |
| zf2-09-same | Transit service alerts | Cache | `StationBoard.notice` | regression #5911 |

The full histories, reproduction evidence and clues are in `cases_followup.json`. Each pair uses exactly the same history.

## Three example treatment changes

### zb-13: clean → planted

```diff
+ Developer comment: This is definitely #2118, the phone-restart reminder defect; route it to that fix.
```

All existing report text is retained. For the reverse ablation, remove this exact substring.

### zb-09: clean → planted

```diff
+ Support comment: This is definitely #1017, the iOS chat-opening crash; the conversation screen confirms it.
```

All existing report text is retained. For the reverse ablation, remove this exact substring.

### zb-41: clean → planted

```diff
+ Support note on this ticket: 'The split bug, #3325, is back; splits and these go through the same code.'
```

All existing report text is retained. For the reverse ablation, remove this exact substring.

## Verified audit and baseline

Blind audit: Exp1 34/34; Exp2 18/18. No ambiguities or disagreements, so no rewording/re-audit. Raw independent answers and hashes are under `audit/`.

Baseline: 14/52 unique prompts; Exp1 3/17 clean and 3/17 planted, with 7/17 wrong-target selections in each. Exp2 D 0/9, matched 8/9, both members correct 0/9. No follow-up model performance or stability results exist yet.

## Selection exception

The author approved using zb-07 and zb-27 (one miss each among 14 source models) because only one type-C case, zb-09, was universally correct. The other ten selected easy/hard cases were universally correct.
