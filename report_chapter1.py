import docx
from docx.shared import Inches, Pt, RGBColor
from report_styles import add_p, add_body, add_h1, add_h2, add_h3, add_bullet

def generate_chapter_1(doc):
    # CHAPTER 1
    add_h1(doc, "CHAPTER 1\nINTRODUCTION")
    
    # 1.1 Background
    add_h2(doc, "1.1 Background of Flood Disaster & Crisis Logistics")
    add_body(doc, "Urban pluvial and fluvial flooding represent some of the most catastrophic and economically destabilizing natural disasters confronting modern metropolitan areas worldwide. In coastal cities characterized by rapid urbanization, high population densities, and low-lying topography, extreme precipitation events frequently overwhelm traditional drainage infrastructure, submerging vital transportation arteries, cutting off residential enclaves, and precipitating severe humanitarian crises. The city of Chennai, situated on the Coromandel Coast in southeastern India (latitude 13.0827° N, longitude 80.2707° E), epitomizes these extreme vulnerabilities.")
    
    add_body(doc, "Chennai is naturally drained by three primary watercourses—the Adyar River in the south, the Cooum River traversing the urban core, and the Kosasthalaiyar River to the north—interconnected by the historic Buckingham Canal and Otteri Nullah drainage channels. The city is subject to the intense Northeast Monsoon season between October and December, which delivers over sixty percent of its total annual precipitation in concentrated, high-intensity convective and cyclonic episodes. Over the past three decades, rapid real estate expansion, encroachment on natural floodplains, marshlands (such as the Pallikaranai marsh), and arterial water bodies have severely impaired the natural hydrological retention capacity of the Chennai basin.")
    
    add_body(doc, "The human and economic consequences of these hydro-meteorological imbalances were demonstrated during the catastrophic December 2015 Chennai floods, during which extreme rainfall (exceeding 490 mm in 24 hours) overwhelmed the Chembarambakkam reservoir catchment, inundating over 100,000 homes, stranding millions of citizens, and resulting in over 400 casualties and five billion US dollars in infrastructural damages. More recently, in December 2023, Severe Cyclonic Storm Michaung stalled off the coast of north Tamil Nadu, releasing unprecedented localized downpours exceeding 450 mm over two days. Once again, extensive neighborhoods across North Chennai (Manali, Korattur, Vyasarpadi) and South Chennai (Velachery, Madipakkam, Perumbakkam) remained submerged under one to two meters of stagnant floodwaters for multiple days.")
    
    add_body(doc, "In the immediate aftermath of such catastrophic events, emergency crisis logistics becomes the sole determinant of human survivability. The primary objective of disaster logistics is the rapid, equitable, and safe transport of essential survival commodities—specifically potable drinking water, dry food rations, and acute emergency medical care kits—from central logistics hubs and district warehouses to displaced populations residing in designated relief shelters and marooned neighborhood clusters. Concurrently, emergency managers must coordinate the safe evacuation of vulnerable citizens (the elderly, infants, and individuals with severe medical conditions) along safe, non-submerged transit corridors.")
    
    # 1.2 Problem Statement
    add_h2(doc, "1.2 Problem Statement")
    add_body(doc, "Despite decades of institutional evolution within national and state disaster response authorities, emergency operations centers (EOCs) during major urban flood events continue to suffer from fundamental technological and operational bottlenecks. Contemporary municipal flood management exhibits three acute points of failure:")
    
    add_bullet(doc, "Information Disconnect and Reactive Response", 
               "Municipal emergency coordinators rely primarily on post-incident distress calls, unverified social media reports, and manual telephone reports from ward officials. Consequently, relief supplies are dispatched reactively hours or days after local reserves are exhausted, rather than proactively staged ahead of imminent flood crests.")
    
    add_bullet(doc, "Static Rule-Based Demand Estimation", 
               "Standard municipal logistics calculations apply coarse, one-size-fits-all per-capita estimation formulas (e.g., allocating a uniform 3.0 liters of water and two generic meal packets per registered evacuee) without considering localized flood severity, household socioeconomic vulnerability, demographic elderly-to-child ratios, water contamination indices, or multi-day accumulation factors. This leads to severe localized stockouts in densely populated, low-income informal settlements alongside wasteful over-allocation at accessible city-center facilities.")
    
    add_bullet(doc, "Hazard-Blind Logistics and Routing Failures", 
               "Conventional emergency routing relies on commercial GIS software or general-purpose navigation engines (such as Google Maps or standard OpenStreetMap routers) that compute shortest paths based solely on static road distance or normal traffic congestion. These engines lack real-time coupling with localized hydrological inundation depths. As a consequence, high-capacity relief trucks and emergency rescue convoys are frequently routed through low-lying arterial underpasses and canal bridges submerged under lethal depths of floodwater (>0.60 m), resulting in vehicle stranding, engine hydro-locking, wasted operational fuel, and catastrophic delays in life-saving interventions.")
    
    add_body(doc, "Consequently, there is an urgent societal and engineering need for an integrated, intelligent, and mathematically rigorous decision-support platform that couples meteorological hazard forecasting, fine-grained multi-commodity demand estimation with formal uncertainty guarantees, exact linear programming allocation, and hazard-aware dynamic graph routing into a unified, sub-second execution framework.")
    
    # 1.3 Motivation
    add_h2(doc, "1.3 Motivation of the Project")
    add_body(doc, "The primary motivation of this project stems from the conviction that modern advances in applied machine learning, mathematical optimization, and open-source geospatial computing can transform disaster response from a chaotic, ad-hoc, reactive process into an exact, proactive, and equitable science. When natural calamities strike, decision-makers in command centers face extreme cognitive overload, conflicting data streams, and immense time pressure. In such environments, relying on heuristics and manual spreadsheet calculations leads to severe allocative biases, where vocal or easily accessible wards receive disproportionate aid while marginalized, physically isolated communities suffer silent neglect.")
    
    add_body(doc, "Furthermore, disaster logistics operates under profound real-world uncertainty. Deterministic machine learning point predictions—such as predicting that a shelter requires exactly 1,250 liters of water—are inherently fragile and fail to communicate model uncertainty to field commanders. A logistics platform designed for life-critical deployment must provide rigorous, distribution-free statistical uncertainty guarantees, enabling logistics directors to provision safe conservative upper bounds without unbounded budgetary waste. Conformal prediction provides a mathematically sound foundation for this requirement, generating calibrated prediction intervals with finite-sample coverage guarantees without requiring unrealistic parametric distribution assumptions.")
    
    add_body(doc, "Finally, technological solutions developed for municipal administration must prioritize practical deployability and inclusivity. Complex computational systems that require supercomputing clusters or hours of numerical convergence are useless during live tactical operations. The platform must execute full multi-step simulations—from meteorological hazard assessment to ward demand regression, depot supply allocation, and evacuation pathfinding—in sub-second latency on standard commodity hardware. Moreover, the actionable outputs must be directly accessible to ground personnel through bilingual interfaces supporting local languages (Tamil and English), clear spatial visualizations, and offline-capable municipal atlases.")
    
    # 1.4 Objectives
    add_h2(doc, "1.4 Objectives of the Project")
    add_body(doc, "To address the identified challenges, this project formulates six explicit, verifiable technical objectives:")
    
    add_bullet(doc, "Objective 1: Spatio-Temporal Hydro-Meteorological Ingestion", 
               "To ingest, clean, and structure 25 years (9,131 daily records from 2001 to 2025) of NASA POWER satellite and atmospheric reanalysis data for the Chennai metropolitan coordinate (13.0827° N, 80.2707° E), engineering 7-day rolling statistical windows, lagged precipitation aggregations, and cyclic trigonometric day-of-year seasonal encodings.")
    
    add_bullet(doc, "Objective 2: Machine Learning Precipitation Hazard Classification", 
               "To formulate, train, and validate a 180-tree Gradient Boosted Decision Tree (GBDT) binary classification pipeline capable of predicting next-day heavy rainfall hazard (>=10 mm/day threshold) with verified holdout ROC-AUC >= 0.85 and operational recall >= 80% on a completely untouched four-year test set (2022–2025).")
    
    add_bullet(doc, "Objective 3: Multi-Commodity Disaster Demand Ensemble Modeling", 
               "To architect a 128-tree multi-output ensemble (combining 64 Extra Trees, 64 Random Forest regressors, and L2-regularized Ridge regression) trained across 55,000 spatial disaster scenario records representing all 200 Greater Chennai Corporation (GCC) wards, achieving an MAE error reduction greater than 80% compared to standard municipal planning baselines under strict disaster-group holdout evaluation (Cyclone Michaung).")
    
    add_bullet(doc, "Objective 4: Distribution-Free Finite-Sample Uncertainty Calibration", 
               "To implement an inductive split-conformal prediction calibration framework using 9,622 independent holdout records, mathematically proving and empirically validating 90% finite-sample prediction interval coverage across emergency drinking water, food rations, and medical supply predictions.")
    
    add_bullet(doc, "Objective 5: Exact Multi-Commodity Supply Optimization", 
               "To formulate and solve a multi-facility, multi-commodity linear programming model using Google OR-Tools GLOP, optimizing resource flows from 5 central distribution depots to 12 designated emergency shelters while enforcing warehouse conservation laws, shelter priority weighting, and non-negativity constraints.")
    
    add_bullet(doc, "Objective 6: Hazard-Aware Dynamic Evacuation Graph Routing & GIS Integration", 
               "To construct a topological graph representation of Chennai's arterial road network in NetworkX, dynamically filtering edges exceeding physical submersion thresholds (0.50 m for pedestrian rescue, 0.30 m for standard logistics trucks), and integrating the end-to-end pipeline into a sub-second (<0.45s) Next.js 14 / FastAPI geospatial operations dashboard supporting automated bilingual Tamil/English advisories and an offline 200-ward atlas.")
    
    # 1.5 Scope
    add_h2(doc, "1.5 Scope of the Project")
    add_body(doc, "The scope of this project is demarcated by the following technical and operational boundaries:")
    
    add_bullet(doc, "Geographic Scope", 
               "The platform covers the entire administrative territory of the Greater Chennai Corporation (GCC), encompassing all 200 electoral wards across 15 administrative zones (Zones I to XV: Thiruvottiyur to Sholinganallur), covering an area of 426 square kilometers and a baseline population of approximately 7.1 million residents.")
    
    add_bullet(doc, "Logistics Network Topology", 
               "The optimization engine models 5 strategic municipal logistics warehouses (Central Depot, North Depot, South Depot, West Depot, and Airport Logistics Hub), 12 designated primary municipal evacuation shelters, and 10 secondary neighborhood distribution points.")
    
    add_bullet(doc, "Commodity Scope", 
               "The system focuses strictly on life-sustaining primary emergency relief commodities: potable drinking water (measured in liters), ready-to-eat dry food rations (measured in meal units), and acute disaster medical emergency care kits (containing trauma dressings, oral rehydration salts, water purification tablets, and essential antibiotics).")
    
    add_bullet(doc, "Decision-Support Boundary", 
               "The platform functions as an intelligent decision-support system (DSS) for municipal commissioners, district disaster management authorities (DDMA), and emergency response coordinators. The system outputs optimal supply schedules, dispatch manifests, routing waypoints, and bilingual bulletins. The actual physical dispatch of vehicles and execution of evacuation remains under the command of human operational authorities.")
    
    doc.add_page_break()
