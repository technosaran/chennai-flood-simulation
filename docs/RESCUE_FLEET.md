# Limited rescue fleet — 18 October 2026

The finite-fleet feature supplements ground evacuation with a dedicated provisional rescue-transfer schedule. It does not dispatch assets or count estimates as completed rescues.

## Constraints and algorithm

- Inputs: truck/boat/helicopter pools with count, seats, speed, loading/unloading minutes and readiness delay; a common Chennai base; a 15–240 minute planning window. Pool counts are 0–20, combined maximum 30. Inputs reject nonfinite values and out-of-bounds bases.
- Demand: the snapshot's unassigned/isolated cluster population, after the existing ground shelter planner.
- Destinations: non-compromised shelters with remaining capacity and modeled ground depth below 0.30 m. Reservations cannot exceed these residual spaces.
- Trucks: base, pickup and destination must be below 0.30 m and a path must exist in the 0.30 m closure graph. Geometry including access connectors is sampled at intervals of at most 25 m. This is conservative for elevated road segments and cannot establish real safety.
- Boats: pickup depth at least 0.30 m; transport uses a direct-distance proxy. Continuous navigable water, flow velocity, launch/docking access and land-transfer requirements are not verified.
- Helicopters: direct-distance proxy; hoist, landing, weather and airspace feasibility are not verified.
- Each vehicle starts after its readiness delay. A trip includes base-to-pickup travel, loading, pickup-to-shelter travel and unloading. Service counts only when drop-off completes within the window. Return-to-base travel determines the next departure time. Vehicles may still be returning when the window ends.
- A priority queue schedules the earliest available vehicle. Compatible demand is prioritized by modeled depth, then earliest drop-off. The heuristic is deterministic and is not a globally optimal vehicle-routing solution.
- Per-cluster demand and per-shelter slots decrease within the plan. Trips never exceed vehicle seats; vehicles cannot overlap trips. Remaining demand includes an explicit capacity/access/time reason.

## Snapshot semantics

All hours remain independent scenarios. Fleet activity and rescued-person identities are not propagated from one snapshot to the next. Flood conditions are frozen through each window; a route open at its start may not remain open. The existing ground assignments and cumulative supply ledger are preserved. Rescue reservations do not update shelter occupancy or relief demand, because they are provisional plans. The separately modeled supply transport fleet remains unconstrained by these rescue counts.

API responses expose `timeline[].rescue_fleet_plan`. The submitted configuration is retained in `scenario.rescue_fleet`. Existing API callers can omit the optional configuration. Frontend runs submit the configured defaults. Reports include hourly fleet service/remaining demand and configuration; saved experiments restore fleet settings and export comparison metrics.

## Demonstration

1. In Scenario, choose a small flooded circle around a population point with dry shelters elsewhere.
2. Set trucks and boats to zero, one helicopter, and a longer planning window; run.
3. Select a flooded hour and open Relief & Supplies. Inspect provisional service, remaining demand and repeat trips.
4. Set all counts to zero and rerun. Remaining support need equals the initial snapshot rescue demand.
5. Increase fleet count, change seats or readiness delay, and compare outcomes in Experiments. Keep geography and other conditions fixed.

Tests cover seat limits, headcount conservation, shelter reservations, return-before-reuse, deadlines, delayed/zero fleets, extra vehicles, boat depth, blocked truck paths/connectors, flooded/full destinations, invalid configurations and unchanged ground/inventory outputs in integrated runs.

Verification: 99 backend tests, 95 strict live API tests, four report tests and the production frontend build passed. Browser controls were exercised with a T. Nagar scenario and a 90-minute fleet window; at T+3h the configured six trucks, four boats and two helicopters provisionally served 84 of 48,000 people in ten transfers. Remaining support need was 47,916. These are modeled estimates, not completed rescues. Report download was checked on 19 October 2026 and includes fleet outcomes/configuration; an example is saved at `docs/reports/fleet-scenario.html`.
