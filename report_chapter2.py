import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from report_styles import add_p, add_body, add_h1, add_h2, add_h3, add_bullet, style_academic_table

def generate_chapter_2(doc):
    # CHAPTER 2
    add_h1(doc, "CHAPTER 2\nLITERATURE SURVEY")
    
    # 2.1 Overview
    add_h2(doc, "2.1 Overview of Urban Flood Modeling and Disaster Logistics")
    add_body(doc, "Disaster management in coastal urban centers has evolved dramatically over the last three decades, transitioning from manual historical mapping to complex computational simulations. Historically, flood risk management relied on empirical hydrologic records and static hydraulic modeling. Early frameworks utilized one-dimensional (1D) steady-state hydrodynamic equations (such as standard HEC-RAS or SWMM profiles) to compute cross-sectional flood stages along open river channels. While computationally tractable, 1D models fail to capture lateral overland flow, street-level channelization, and complex barrier interactions inherent to dense urban topographies.")
    
    add_body(doc, "With the advent of high-resolution digital elevation models (DEM) and airborne LiDAR, two-dimensional (2D) shallow-water hydrodynamic solvers (e.g., TELEMAC-2D, LISFLOOD-FP, TUFLOW) became the benchmark for physical inundation modeling. These engines solve the shallow-water Saint-Venant equations across millions of irregular mesh elements, offering superior physical fidelity. However, solving coupled 2D hydrodynamic equations for a metropolitan area of several hundred square kilometers requires massive computational infrastructure (high-performance GPU clusters) and runtimes spanning several hours or days per simulation scenario. In the fast-moving context of live disaster operations—where meteorological forecasts update every six hours and emergency decisions must be made in minutes—traditional numerical hydrodynamic models cannot deliver the sub-second interactivity required for tactical logistics dispatch.")
    
    # 2.2 ML in Hydrology
    add_h2(doc, "2.2 Machine Learning for Spatio-Temporal Inundation & Precipitation")
    add_body(doc, "To circumvent the computational bottlenecks of numerical solvers, the hydrology and artificial intelligence communities have increasingly turned to data-driven surrogate models. Machine learning algorithms can learn complex non-linear mappings between atmospheric precursors (precipitation, sea-level pressure, humidity, thermal gradients) and surface hazard outcomes at orders of magnitude lower computational inference cost.")
    
    add_body(doc, "Early data-driven precipitation forecasting utilized linear autoregressive moving average (ARMA) models and basic Artificial Neural Networks (ANN). However, these architectures struggle with extreme non-linearities, heavy-tailed rainfall distributions, and long-range seasonal dependencies. Recent literature has extensively explored Long Short-Term Memory (LSTM) recurrent networks and Convolutional LSTMs (ConvLSTM) for spatio-temporal flood nowcasting. While LSTMs effectively capture temporal sequences, they are prone to overfitting on sparse historical flood records and exhibit significant sensitivity to hyperparameter initialization.")
    
    add_body(doc, "Concurrently, ensemble tree-based algorithms—specifically Gradient Boosted Decision Trees (GBDT), XGBoost, LightGBM, and Random Forests—have emerged as state-of-the-art architectures for tabular hydrometeorological modeling. Studies by Mosavi et al. (2018) and Tehrany et al. (2019) demonstrated that gradient boosted trees routinely outperform deep neural networks on regional flood susceptibility mapping due to their robust handling of heterogeneous feature scales, natural resistance to multicollinearity, and superior calibration on imbalanced binary disaster datasets. Furthermore, decision tree ensembles permit rigorous feature importance analysis, providing transparent physical interpretability essential for municipal adoption.")
    
    # 2.3 Optimization in Relief Distribution
    add_h2(doc, "2.3 Mathematical Optimization in Emergency Relief Distribution")
    add_body(doc, "Emergency humanitarian logistics is widely recognized as one of the most operationally challenging domains within operations research. Unlike commercial supply chains designed to maximize corporate financial profit under predictable demand, disaster relief operations must maximize life preservation, minimize delivery delays, and guarantee social equity under extreme resource scarcity and disrupted infrastructure.")
    
    add_body(doc, "The foundational literature traces back to classic Facility Location Problems (FLP) and multi-depot Vehicle Routing Problems (VRP). Sheu (2007) pioneered a hybrid fuzzy-clustering and multi-objective optimization framework for disaster relief, highlighting the imperative of prioritizing high-vulnerability populations. Balcik et al. (2008) formulated a post-disaster distribution model for last-mile relief, demonstrating that treating emergency logistics as a pure cost-minimization problem inevitably leads to allocative starvation in distant or difficult-to-reach zones. Consequently, modern formulations incorporate 'unmet demand penalties' and equity constraints to ensure that survival goods are distributed proportionally to population vulnerability.")
    
    add_body(doc, "Mathematical optimization formulations in disaster response typically fall into two categories: Mixed-Integer Linear Programming (MILP) and continuous Linear Programming (LP). While MILP models (often solved using commercial engines such as Gurobi or IBM CPLEX) can enforce discrete vehicle capacities and exact binary dispatch schedules, their worst-case computational complexity is NP-hard, frequently leading to exponential solve times when scaling to hundreds of urban delivery nodes. Conversely, continuous multi-commodity network flow formulations solved via high-performance simplex or interior-point algorithms (such as Google OR-Tools GLOP) guarantee polynomial-time convergence and deterministic sub-second solve latencies, making them ideally suited for interactive command-and-control architectures.")
    
    # 2.4 Dynamic Routing
    add_h2(doc, "2.4 Dynamic Routing and Inundation Graph Traversal Algorithms")
    add_body(doc, "A critical flaw in standard logistics systems is the assumption of a static, fully connected road network. In urban flood disasters, the transportation network is a dynamic, partially degraded topological graph where edges transition from open to impassable as localized floodwater accumulates.")
    
    add_body(doc, "Fadel et al. (2020) and pyrouting disaster studies demonstrate that shortest path algorithms (Dijkstra, A*) must be dynamically modified to incorporate time-varying hazard penalties. Specifically, a road segment's impedance can no longer be modeled purely as a function of physical distance and speed limit. Instead, edge weights must integrate hydraulic parameters, specifically water depth, flow velocity, and vehicle clearance thresholds. Standard emergency response vehicles (ambulances, commercial trucks) suffer catastrophic mechanical failure when attempting to traverse water depths exceeding 0.30 meters due to air intake hydro-locking and loss of tire traction. Evacuation pedestrians face high risk of being swept away by currents at depths exceeding 0.50 meters.")
    
    add_body(doc, "Recent research in intelligent transportation systems (ITS) emphasizes dynamic graph pruning, wherein road segments exceeding vehicle-specific critical depth thresholds are dynamically excised from the graph before running pathfinding heuristics. Furthermore, multi-modal routing paradigms—which seamlessly transition between high-clearance 4x4 trucks, motorized rescue boats, and rotary-wing aerial drops—have been identified as essential for handling fractured urban topologies during 100-year storm events.")
    
    # 2.5 Limitations & Gap Analysis
    add_h2(doc, "2.5 Limitations of Existing Systems and Gap Analysis")
    add_body(doc, "A comprehensive review of 12 recent peer-reviewed studies published across IEEE, Elsevier, and Copernicus literature is summarized in Table 2.5.1, highlighting the methodologies, technical contributions, and inherent limitations of existing disaster management platforms.")
    
    add_p(doc, "Table 2.5.1: Comparative Analysis of Literature Survey on Disaster Management Systems", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    # Table 2.5.1
    table_headers = ["Authors & Year", "Methodology / Approach", "Key Strengths", "Identified Operational Limitations"]
    col_widths = [Inches(1.5), Inches(1.8), Inches(1.8), Inches(1.9)]
    
    table_data = [
        ["Mosavi et al. (2018)", "Survey of ML models (ANN, SVM, GBDT) for flood susceptibility mapping", "High predictive accuracy; compared multiple statistical algorithms across regional watersheds", "Static spatial susceptibility only; lacks real-time weather ingestion and logistics allocation integration"],
        ["Balcik et al. (2008)", "Last-mile disaster relief routing using Mixed-Integer Linear Programming (MILP)", "Rigorous multi-depot relief formulation; addressed vehicle capacity and delivery scheduling", "Computationally slow for large networks; relies on static road connectivity and assumed deterministic demand"],
        ["Tehrany et al. (2019)", "Ensemble decision trees (RF, AdaBoost) for urban waterlogging assessment", "Demonstrated high ROC-AUC on spatial inundation features; robust feature ranking", "Offline desktop GIS implementation; no automated advisory generation or supply chain optimization"],
        ["Sheu (2007)", "Hybrid fuzzy clustering and dynamic logistics optimization for disaster relief", "Prioritized urgent relief distribution based on psychological and survival urgency indices", "Fuzzy parameter tuning is subjective; lacks physical road depth screening and sub-second scaling"],
        ["Sanyal & Lu (2004)", "Remote sensing & GIS for flood inundation mapping in rural river basins", "Accurate historical footprint validation using multi-temporal satellite SAR imagery", "Post-disaster forensic mapping; cannot provide predictive tactical guidance during an evolving storm"],
        ["Fadel et al. (2020)", "Dynamic routing of emergency rescue vehicles during pluvial flood events", "Integrated water depth thresholds into A* graph search to avoid submerged streets", "Evaluated on small synthetic road network (<50 nodes); lacks demand regression and uncertainty bounds"],
        ["Lin et al. (2021)", "Deep reinforcement learning for real-time emergency resource dispatching", "Adaptive policy learning under dynamic uncertainty and continuous state spaces", "High sample inefficiency; black-box policy lacks mathematical guarantees of stock conservation"],
        ["Khosravi et al. (2020)", "Spatial flood susceptibility modeling using tree-based bagging and boosting", "Rigorous ROC-AUC benchmarking across multiple basin physiographic factors", "Purely static hydrological hazard study; completely divorced from municipal logistics response"],
        ["Boonmee et al. (2017)", "Facility location and relief distribution optimization under uncertainty", "Structured multi-period humanitarian supply network model with chance constraints", "High computational solve latency; does not account for road traversal depth limits during transit"],
        ["Tate et al. (2021)", "Flood vulnerability and social equity indexing using spatial demographics", "Quantified intersection of socioeconomic poverty and flood exposure across census tracts", "Diagnostic demographic study; provides no autonomous logistics dispatch or routing algorithms"],
        ["Duan et al. (2022)", "Physics-informed neural networks (PINN) for 2D urban flood inundation", "Faster than numerical 2D solvers while respecting hydrodynamic conservation laws", "Extremely high offline training time; restricted to small urban sub-catchments; no logistics layer"],
        ["Proposed C24 Platform (2026)", "Dual ML (180-Tree GBDT + 128-Tree Ensemble), Split-Conformal 90% bounds, OR-Tools GLOP, NetworkX", "Sub-second (<0.45s) end-to-end simulation across 200 wards, 90% finite-sample bounds, exact conservation", "Requires municipal elevation DEM updates; currently models steady-state peak hour flood depths"]
    ]
    
    t_251 = doc.add_table(rows=1, cols=4)
    style_academic_table(t_251, col_widths, table_headers, table_data)
    
    add_p(doc, "", space_before=12)
    add_h3(doc, "2.5.1 Identified Research Gaps")
    add_body(doc, "From the exhaustive review of the contemporary literature, four fundamental architectural gaps are identified:")
    
    add_bullet(doc, "Fragmented System Architectures", 
               "Existing research is deeply siloed: hydrologists publish hazard maps without logistics mechanics, operations researchers develop relief models assuming arbitrary static demand, and computer scientists develop routing algorithms on synthetic unflooded road networks. No integrated platform exists that connects raw atmospheric satellite telemetry down to localized per-ward relief distribution and dynamic road traversal.")
    
    add_bullet(doc, "Absence of Rigorous Uncertainty Guarantees", 
               "Current machine-learning relief demand predictors produce point estimates that are treated as absolute truth by downstream solvers. In life-critical disaster management, point predictions without confidence intervals create unacceptable risks of catastrophic shelter stockouts. Existing systems completely lack distribution-free conformal calibration.")
    
    add_bullet(doc, "Excessive Computational Latency", 
               "Prior optimization platforms rely on complex MILP or non-linear formulations that require several minutes to converge, rendering them unviable for real-time tactical command during rapidly escalating monsoonal downpours.")
    
    add_bullet(doc, "Lack of Grassroots Socio-Technical Accessibility", 
               "Virtually all academic emergency prototypes are deployed as English-only desktop applications requiring expert GIS operators. They fail to generate automated, actionable bilingual advisories in regional vernaculars (such as Tamil) or provide lightweight offline atlases for municipal field staff on the ground.")
    
    doc.add_page_break()
