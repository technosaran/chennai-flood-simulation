# Recent IEEE base papers for Chennai Flood Lab

Verified and downloaded: 22 October 2026. Both papers are IEEE Access journal articles available as open-access full text. College/library access is unnecessary for these papers. The original publisher PDFs have not been edited.

## Recommended primary paper: closest overall flood/evacuation match (2024)

R. Asriandi Ekaputra, S.-H. Kee, and J.-J. Yee, "Optimizing Urban-Scale Evacuation Strategies Through Disaster Victim Aggregation Modification," IEEE Access, vol. 12, pp. 73581-73598, 2024.

Published: 23 May 2024.
DOI: https://doi.org/10.1109/ACCESS.2024.3404406
IEEE record: https://ieeexplore.ieee.org/document/10537200
Downloaded PDF: Supporting_Paper_IEEE_2024_Urban_Evacuation.pdf (18 pages).

Despite the supporting-paper filename assigned during comparison, this is the recommended primary paper for the overall flood/evacuation project. The filename is retained to avoid creating duplicate deliverables.

### Why it fits

The full paper describes a flood-induced evacuation framework using a 100-year flood-risk map, OSM building information for population estimation, emergency shelter locations and OSM road networks. It groups affected populations using K-means, DBSCAN and ensemble clustering, then evaluates evacuation scenarios in simulation. It therefore overlaps directly with the project's geospatial population representation, road-network inputs, shelters, evacuation simulation and analysis of response outcomes.

### Honest comparison

| Component | Paper | Current project |
| --- | --- | --- |
| Flood context | Flood-risk mapping and evacuation scenarios | Configurable Chennai flood scenarios |
| Geographic road data | OpenStreetMap | Imported Chennai OSM graph |
| Population representation | Clustering and aggregation | Modeled population clusters |
| Shelters and evacuation | Shelter locations and evacuation simulation | Capacity-constrained assignments and route planning |
| Machine learning | Unsupervised clustering | Relief-demand regression and next-day rainfall classification |
| Relief supplies and inventory | Not the central contribution | Water, food and medical supplies, with stock accounting |
| Rescue fleet | Not a basis for claiming equivalent fleet behavior | Provisional truck, boat and helicopter plans |
| Interface and persistence | Do not claim implementation equivalence | Interactive map, timeline, offline atlas and saved simulations |

The project does not reproduce the paper's ensemble-clustering algorithm. Its learned demand models estimate different targets. Neither overlap nor extra features establishes superior performance without a controlled comparison.

## Supporting paper: newer AI/optimization and logistics match (2025)

I. Hssini, "Distributionally Robust and Learning-Based Vehicle Routing for Disaster Blood Logistics," IEEE Access, vol. 13, pp. 119538-119550, 2025.

Published: 30 June 2025.
DOI: https://doi.org/10.1109/ACCESS.2025.3584213
IEEE record: https://ieeexplore.ieee.org/document/11059272
Downloaded PDF: Base_Paper_IEEE_2025_Disaster_Logistics.pdf (13 pages).

This paper combines distributionally robust offline planning with contextual-bandit learning for adaptive dispatch. It coordinates ambulances, drones and ground robots under uncertain demand and disrupted transport conditions, and evaluates service, delay and robustness in simulations. It is a useful foundation for discussing the project's demand uncertainty, relief delivery and heterogeneous fleet planning.

The application is blood delivery, not Chennai flood evacuation. Its contextual-bandit policy and distributionally robust optimization are different from the project's tree-based demand estimates, split-conformal intervals and routing/allocation solvers. Its transport modes also differ. It should not be presented as implementing the same methods or covering the complete project.

If the guide requires 2025 or later, use this as the main logistics-method paper and retain the 2024 evacuation paper as supporting literature. Explicitly explain the adaptation from blood delivery to flood-relief planning.

## Suggested review explanation

"Our primary base paper studies city-scale evacuation during flood scenarios using GIS, road networks, shelters, population aggregation and simulation. Our project applies related planning concepts to Chennai and adds relief-demand estimation, inventory allocation, modeled inundation-dependent routing, provisional multimodal rescue plans and an interactive dashboard. A second IEEE paper supports our discussion of learning-assisted routing and disaster logistics under uncertainty."

## Previous candidates

The 2026 integrated location-inventory-allocation and evacuation paper (DOI: 10.1109/TITS.2026.3697722) remains relevant background, but its PDF was inaccessible with the available account. It is not the practical primary recommendation when a downloadable full text is required. The previously downloaded 2020 IEEE forecasting article is background literature. The Springer article does not satisfy the IEEE requirement.

## Research limits

The current project is an academic scenario simulator. Relief-demand training labels are synthetic; the separate rainfall model uses NASA POWER reanalysis. Do not claim real-time flood forecasting, operational dispatch, replication of either paper or demonstrated superiority. Full-text methods and results should be cited accurately, and paraphrases should not be labeled as verbatim abstracts.
