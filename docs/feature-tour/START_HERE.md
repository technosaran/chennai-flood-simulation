# Chennai Flood Lab: your practical feature tour

Completed in the running app on 22 October 2026. Open http://localhost:3000. On the narrow browser view, click the top-left menu icon to find the sections. After restarting your computer, run `start_project.bat` from the project folder first.

## Start with the examples already prepared for you

Open **Saved runs**, find one of these names, and click **Open saved view**:

| Saved example | What to demonstrate |
| --- | --- |
| Feature tour - baseline with supplies | Velachery, 140 mm/hour, 2.2 m depth, 6 hours; includes a manual allocation of 100 L water and one medical kit to Jawaharlal Nehru Stadium. |
| Feature tour - lower rainfall 50 mm per hour | Same flood zone, depth, spread, duration and fleet as the baseline; lower rainfall. |
| Feature tour - custom circle and adjusted fleet | A manually placed 1.5 km circle, 1.2 m depth, 150 m/hour spread and 4-hour duration; 2 trucks, 2 boats, 1 helicopter and a 90-minute planning window. The selected location contains no modeled population points, so affected population is zero. This is not evidence that the real location has no residents. |
| Feature tour - custom polygon | A manually drawn three-corner polygon; demonstrates impact charts and actual scheduled fleet transfers at hour 1. |
| Feature tour - Adyar without rescue vehicles | Adyar Basin Surge with all dedicated rescue vehicle counts set to zero. |

There is also an imported copy of the baseline, labeled **Imported file**. It demonstrates backup restoration. The copy preserves the full result but treats file-supplied evidence as not independently verified.

Saved views are read-only. Click **Run simulation** to make a new editable run from their settings. Rerunning starts a fresh supply ledger; previous manual allocations remain in the saved snapshot, not in the new run.

## Dashboard: inspect the map and timeline

1. Open a saved example, then open **Dashboard**.
2. Read affected residents, shelter assignments, rescue need and modeled flooded area.
3. Scroll to the timeline and click hours 0, 1 and the last hour.
4. Try **Play**, previous/next steps, and **1x / 2x** speed.
5. Open **Map Layers** to toggle Flood, Evacuation, Supply, Shelters, Depots, Relief points and Population.
6. Click a shelter marker to inspect its status. Click a colored route line to open its transport, distance, estimated time and manifest.
7. Try **Expand map** and restore its size. Use the map's plus/minus controls to zoom.
8. **Load online street tiles** switches to an optional online background; **Use offline map** returns to bundled vectors. The control switched successfully in this session; online tile availability depends on the network.

Route inspection was verified on a truck delivery from Airport Air Cargo Relief Hub to Madipakkam Govt High School Camp: 9.47 km and 10.4 estimated minutes at polygon hour 2. This automatic route had a zero remaining cargo manifest at that hour; it does not prove an actual delivery occurred.

## Scenario: presets, conditions and custom zones

1. Open **Scenario** and choose a **Scenario preset**. Velachery and Adyar were exercised in this tour.
2. Adjust rainfall intensity, peak water depth, flood spread rate and duration.
3. Click **Run simulation** whenever settings change. Wait for the completion notice before inspecting new results.
4. For a circle, choose **Circle Radius**, set its radius and click an empty map position. Existing markers can intercept clicks; choose a position away from a marker.
5. For a polygon, choose **Draw Polygon**, place at least three distinct points, and choose **Finish**. **Undo** removes the last point. Avoid crossing edges.

Circle placement, polygon placement, Undo, Finish and successful simulation runs were verified. The circle and polygon examples are intentionally different geographies and should not be interpreted as a controlled rainfall comparison.

## Relief & supplies: stock and allocation

1. Rerun a scenario to obtain an editable active run.
2. Open **Relief & supplies** and inspect stock, **Shelters**, and **Distribution**.
3. Choose a shelter's **Allocate supplies** or **Allocate Emergency Rations** control, or a relief point's **Dispatch Supplies**.
4. Select a **Source depot** and check that depot's available quantities.
5. Set water, food and medical quantities, then choose **Confirm Allocation** and **Done**.
6. Save a complete simulation afterward if you want to retain the allocation.

The baseline allocation was accepted and the displayed medical inventory decreased by one kit. The UI confirmed that the allocation was recorded in final-step inventory. The water display is rounded in the summary; the full snapshot retains the detailed ledger.

## Rescue fleet: configuration and scheduled trips

1. Under **Scenario → Limited rescue fleet**, expand Trucks, Boats and Helicopters.
2. Set counts, seats, planning speed, handling time, readiness delay, shared base and planning window.
3. Run the scenario, select an hour, then open **Impact** or **Relief & supplies**.
4. Inspect **Rescue fleet availability**, **Vehicle availability at window end**, **Unserved demand**, and **Trip schedule**.

For the saved custom polygon, select **hour 1** in Impact. The 90-minute plan provisionally serves 36 people: two 12-person boat transfers and two 6-person helicopter transfers. The helicopter starts after a 15-minute readiness delay. At hour 2, the safe shelter space is exhausted and no transfers are planned. This demonstrates why vehicle availability alone is insufficient.

These are independent hourly plans, not cumulative rescues or dispatches. The no-vehicle Adyar example is a separate scenario, not a controlled comparison with the polygon.

## Impact: explore the selected hour

Open **Impact**, click an hour on the affected-population chart, and inspect the changing metrics, shelter availability, supply route counts and fleet plan. **Inspect peak exposure** selects the earliest peak-exposure hour. Peak exposure can persist across several hours.

Hourly shelter assignments and fleet plans must not be added together as completed rescues. Comparison columns are separate maxima and can refer to different hours.

## Scenario advice: recommendations and bulletins

Open **Scenario advice** from the menu after a run. Inspect **Priorities**, mark a recommendation reviewed, and explore **Roads**, **Wards**, and **Bulletin**. Advice identifies its final-snapshot hour; it does not follow the chart's selected hour.

English and Tamil bulletin text both displayed and downloaded successfully. **Listen** was attempted for Tamil, but the browser reported **Voice unavailable**. Use the downloaded Tamil text if no suitable voice is installed. No bulletin was sent to anyone. Recommendation review is a local session marker, not an executed rescue action.

## Saved runs: save, restore, compare and export

- **Save complete simulation:** enter a name after a fresh run. Saves the timeline, inputs, allocations and fleet plans.
- **Open saved view:** reopens the archived map and timeline. Verified before and after resetting the active scenario.
- **Download snapshot JSON:** creates a complete portable backup.
- **Restore a backup → Snapshot JSON file → Import snapshot JSON:** restores a downloaded full backup as a new read-only copy. The baseline backup round-trip succeeded.
- **Compare runs:** choose a baseline and comparison. The notebook keeps the last eight summaries in this browser; complete snapshots are stored separately by the backend.
- **Export comparison:** downloads CSV for Excel.
- **Export a scenario report → Download scenario report:** downloads a self-contained HTML report. Open the file and use browser Print → Save as PDF if needed.
- **More options → Export results:** downloads results JSON; this is distinct from a full snapshot backup.
- **More options → Reset scenario:** clears the active view. Saved examples remain available. Reset and reopening the preserved baseline were verified.

The controlled rainfall comparison produced these independent peak values:

| Measure | Baseline: 140 mm/hour | Comparison: 50 mm/hour |
| --- | ---: | ---: |
| Affected residents | 92,500 | 37,000 |
| Shelter assignments | 27,110 | 12,950 |
| Rescue need | 65,390 | 37,000 |
| Flood area | 59.70 km2 | 18.17 km2 |

## Research tools: Ward atlas

Open **Research tools → Ward atlas**, search **Velachery**, then select **Ward 177**. Its included modeled population is 37,000 and it lists nearby planning shelters. Search, selection and profile display worked. The directory contains 200 wards, but most have no modeled population points. Missing coverage is not zero population or zero risk. Shelter proximity is straight-line distance, not a verified safe route.

## Research tools: Model evaluation

1. Open **Model evaluation** and inspect **Real-data rainfall model**.
2. Set **Historical conditions through (UTC)** to **2023-12-02**, then choose **Replay prediction**.
3. The replay targets 2023-12-03: 83.96% estimated probability of rainfall at least 10 mm/day; actual next-day gridded reanalysis was 88.12 mm/day.
4. Review **Deployed model evaluation**, **Refresh evidence**, and **Current run evidence**.
5. Search **Likely panel questions** for **dataset** and expand the answer.
6. Choose **Download panel guide** for viva preparation.

The weather experiment uses NASA POWER gridded historical reanalysis. The separate relief-demand model uses synthetic labels. Model evidence is not real-flood forecasting validation.

## Help and keyboard reference

The **Help** dialog and **More options → Keyboard shortcuts** opened successfully. Some wording in those dialogs still uses older screen names or describes a fixed six-hour timeline; follow the current sidebar names and your configured duration. Use the visible controls for this tour. This session did not verify every keyboard shortcut or every preset/parameter combination.

## Files collected in this folder

- `baseline-report.html`: exported baseline report with the manual allocation.
- `baseline-full-snapshot.json`: complete portable baseline backup; also successfully imported.
- `rainfall-comparison.csv`: comparison notebook export taken after the lower-rainfall experiment.
- `polygon-results.json`: results export from the custom polygon.
- `panel-guide.md`: panel/viva guide exported by the app.
- `bulletin-english.txt` and `bulletin-tamil.txt`: sample scenario bulletins.
- PNG screenshots: saved examples, comparison, fleet trips, route inspector, ward atlas, weather model and Tamil voice fallback.

This is an interactive feature tour, not an exhaustive audit of every setting. Earlier in this conversation, 115 backend tests, 95 live API tests, five report tests and frontend type checking passed. Those checks were not rerun during this UI tour because the application code was not changed.
