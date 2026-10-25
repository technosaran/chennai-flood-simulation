import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from report_styles import add_p, add_body, add_h1, add_h2, add_h3, add_bullet, add_fig, style_academic_table
import os

def generate_chapter_3(doc):
    # CHAPTER 3
    add_h1(doc, "CHAPTER 3\nPROPOSED SYSTEM")
    
    # 3.1 Existing System Overview
    add_h2(doc, "3.1 Existing System Overview & Operational Bottlenecks")
    add_body(doc, "The prevailing disaster management infrastructure deployed across Indian coastal municipalities—including the Greater Chennai Corporation (GCC) and the Tamil Nadu State Disaster Management Authority (TNSDMA)—operates predominantly as a reactive, manual command-and-control hierarchy. Under standard operational protocols, when an extreme weather warning is issued by the India Meteorological Department (IMD), municipal emergency operation centers (EOCs) convene inter-departmental coordination meetings involving revenue, public works, police, and fire & rescue personnel.")
    
    add_body(doc, "However, the digital workflows supporting this response suffer from severe operational bottlenecks:")
    
    add_bullet(doc, "Manual Spreadsheet Record-Keeping", 
               "Logistics inventories across central warehouses, regional distribution depots, and designated relief shelters are tracked via ad-hoc spreadsheet entries or physical registers. Data entry occurs asynchronously through phone calls and field inspections, introducing substantial reporting latencies (typically 6 to 12 hours behind ground realities) and human transcription errors.")
    
    add_bullet(doc, "Coarse Per-Capita Planning Rules", 
               "Emergency supply allocations rely on static municipal formulas established during non-emergency census enumerations. For example, municipal planning guidelines mandate a blanket allocation of 3.0 liters of drinking water and 2 dry food packets per registered evacuee per day, irrespective of whether the neighborhood is experiencing minor street waterlogging (0.10 m) or severe residential submergence (1.50 m) with severed electrical and water supply lines. This heuristic approach completely fails to capture the non-linear surge in drinking water and emergency medical demand caused by groundwater contamination, power outages, and waterborne disease outbreaks.")
    
    add_bullet(doc, "Hazard-Blind Routing & Delayed Dispatches", 
               "Emergency truck drivers and rescue boat convoys are dispatched using static city road maps or generic navigation smartphone applications. When key arterial underpasses (e.g., Gengu Reddy subway, Vyasarpadi subway, or Madipakkam junctions) are submerged under deep water, convoys encounter sudden road closures, forcing blind backtracking, causing hours of delay, and frequently stranding heavy rescue vehicles.")
    
    # 3.2 Implementation Environment
    add_h2(doc, "3.2 Implementation Environment")
    add_body(doc, "The proposed platform is engineered using modern, high-performance, open-source software libraries and robust development environments to guarantee sub-second execution, cross-platform portability, and zero-licensing cost for municipal deployment. Table 3.2.1 provides the comprehensive hardware and software specifications utilized during platform development and benchmarking.")
    
    add_p(doc, "Table 3.2.1: Implementation Environment Specifications", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    env_headers = ["Category", "Component / Specification", "Version / Model", "Operational Role in Platform"]
    env_widths = [Inches(1.5), Inches(2.0), Inches(1.2), Inches(2.3)]
    env_data = [
        ["Hardware", "Central Processing Unit (CPU)", "AMD Ryzen 5 / Intel Core i7", "High-throughput parallel tree inference and graph solving"],
        ["Hardware", "System Memory (RAM)", "16 GB DDR4 Dual-Channel", "In-memory caching of 200 GCC ward GeoJSONs and 55K scenario matrix"],
        ["Hardware", "Storage", "512 GB NVMe SSD (PCIe 4.0)", "Sub-millisecond disk I/O for historical weather datasets and models"],
        ["Operating System", "Host Operating System", "Windows 11 / Ubuntu 22.04 LTS", "Cross-platform deployment environment for containerized services"],
        ["Programming", "Core Backend Language", "Python 3.12.x", "Implementation of machine learning, linear programming, and graph APIs"],
        ["Programming", "Frontend Language & Runtime", "TypeScript / Node.js 20.x", "Type-safe client-side state management and reactive rendering"],
        ["Backend Framework", "REST API Web Framework", "FastAPI 0.115+", "Asynchronous, high-concurrency web endpoints with OpenAPI schemas"],
        ["Backend Server", "ASGI Application Server", "Uvicorn 0.32+", "High-performance asynchronous server running on uvloop"],
        ["ML Framework", "Machine Learning & Preprocessing", "scikit-learn 1.5+", "GBDT classifier, ExtraTrees ensemble, Ridge regression, scalers"],
        ["Optimization", "Linear Programming Solver", "Google OR-Tools 9.10+ (GLOP)", "Sub-second continuous multi-commodity supply allocation solver"],
        ["Graph Engine", "Network Analysis & Pathfinding", "NetworkX 3.3+", "Dynamic road impedance calculation and thresholded Dijkstra routing"],
        ["Geospatial", "GIS Geometry & GeoJSON", "Shapely 2.0+ / GeoPandas 1.0+", "Spatial polygon containment, buffer analysis, and ward boundaries"],
        ["Frontend UI", "Modern Web Framework", "Next.js 14 (App Router) / React 18", "Server-side rendering, client hydration, and dynamic routing"],
        ["Frontend UI", "CSS Styling & Component System", "Tailwind CSS 3.4+ / Lucide Icons", "Responsive disaster dashboard design for desktop and mobile displays"],
        ["Mapping", "Interactive Spatial Visualization", "Leaflet 1.9+ / React-Leaflet", "Client-side vector flood heatmaps, shelter pins, and route polylines"]
    ]
    
    t_321 = doc.add_table(rows=1, cols=4)
    style_academic_table(t_321, env_widths, env_headers, env_data)
    
    add_p(doc, "", space_before=12)
    # 3.3 Proposed Methodology
    add_h2(doc, "3.3 Proposed Methodology")
    add_body(doc, "The proposed AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform establishes a closed-loop, data-driven methodology that unifies atmospheric physics, predictive machine learning, mathematical optimization, and spatial graph theory. The operational methodology proceeds through five cohesive phases:")
    
    add_bullet(doc, "Phase 1: Multi-Source Spatio-Temporal Data Ingestion", 
               "The platform ingests 25 years of daily atmospheric reanalysis data (NASA POWER) for Chennai, alongside detailed GIS spatial topologies (200 GCC administrative ward boundaries, road networks, 12 evacuation shelters, 5 central depots, and 10 distribution hubs). Features undergo rolling temporal aggregation, missing-value imputation, and cyclic trigonometric encoding.")
    
    add_bullet(doc, "Phase 2: Predictive Hazard & Demand Modeling", 
               "A dual machine learning pipeline is executed. The 180-tree GBDT model classifies next-day heavy precipitation hazard (>=10 mm/day). Simultaneously, the 128-tree multi-output ensemble (ExtraTrees + RandomForest + Ridge) infers per-capita emergency drinking water, food, and medical kit requirements across all 200 wards based on simulated flood depth, population density, vulnerability index, and outage severities.")
    
    add_bullet(doc, "Phase 3: Finite-Sample Uncertainty Calibration", 
               "To eliminate dangerous under-allocation risks, the platform applies distribution-free split-conformal prediction. Nonconformity error residuals calculated on 9,622 holdout calibration records generate mathematically guaranteed 90% finite-sample prediction intervals, providing field commanders with conservative, risk-hedged demand bounds.")
    
    add_bullet(doc, "Phase 4: Multi-Commodity Supply Optimization", 
               "Using Google OR-Tools GLOP linear programming, the platform models supply conservation across all 5 municipal warehouses, solving an exact objective function that minimizes unmet relief demand penalized by shelter vulnerability weights, guaranteeing equitable allocation without exceeding inventory stocks.")
    
    add_bullet(doc, "Phase 5: Hazard-Aware Dynamic Routing & Actionable Dissemination", 
               "The road network is converted to a dynamic graph in NetworkX. Road edges submerged beyond critical vehicular clearance thresholds are pruned, and optimal evacuation and dispatch routes are computed. Finally, automated bilingual bulletins (Tamil and English) and offline PDF/HTML atlases are generated for immediate tactical execution.")
    
    # 3.4 System Architecture
    add_h2(doc, "3.4 System Architecture")
    add_body(doc, "The system architecture is organized into a modular, decoupled 7-tier pipeline designed for high resilience, testability, and sub-second execution speed. Figure 3.4.1 illustrates the architectural components and data flow across all seven tiers.")
    
    # Add Figure 3.4.1
    add_fig(doc, r"generated_charts\architecture_flow.png", 
            "Figure 3.4.1: Layered 7-Tier System Architecture Diagram", width=Inches(6.0))
    
    add_body(doc, "The architectural tiers operate as follows:")
    
    add_bullet(doc, "Tier 1: Data Ingestion & Atmospheric Processing", 
               "Harvests daily reanalysis variables from NASA POWER and local rain gauges. Constructs temporal feature arrays, rolling statistical summaries (7-day means, maxes, sums), and cyclical calendar encodings.")
    
    add_bullet(doc, "Tier 2: Hazard Classification Engine", 
               "Hosts the 180-tree Gradient Boosted Decision Tree (GBDT) model. Processes real-time atmospheric feature vectors to output binary heavy rainfall hazard probabilities (P >= 0.50 thresholded).")
    
    add_bullet(doc, "Tier 3: Multi-Commodity Demand Forecasting", 
               "Hosts the 128-tree multi-output ExtraTrees/RandomForest/Ridge regression blend. Maps ward-level flood depth, population, and socio-economic vulnerability to predicted liters of water, food packets, and medical kits.")
    
    add_bullet(doc, "Tier 4: Conformal Calibration & Statistical Bounds", 
               "Applies inductive split-conformal quantile calibration to output distribution-free 90% prediction intervals [Lower_Bound, Upper_Bound] for each commodity, preventing shelter stockout.")
    
    add_bullet(doc, "Tier 5: Mathematical Supply Chain Optimizer", 
               "Encapsulates Google OR-Tools GLOP. Formulates and solves the multi-commodity network flow model, balancing depot inventories, transport impedances, and shelter urgency weights.")
    
    add_bullet(doc, "Tier 6: Dynamic Network Routing & Evacuation Solver", 
               "Evaluates road network edge traversability against physical water depth thresholds (0.30 m for logistics trucks, 0.50 m for rescue personnel), dynamically allocating routes across trucks, boats, and aerial drops.")
    
    add_bullet(doc, "Tier 7: Operational Interface & Bilingual Dissemination", 
               "Renders the responsive Next.js 14 web GIS console, executing interactive scenario replays, generating automated Tamil/English public bulletins, and compiling standalone municipal atlases.")
    
    # 3.5 Module Design
    add_h2(doc, "3.5 Module Design & End-to-End Pipeline")
    add_body(doc, "The platform decomposes disaster response into six synchronized operational stages. Figure 3.5.1 illustrates the linear and feedback pathways connecting raw weather telemetry to field execution.")
    
    # Add Figure 3.5.1
    add_fig(doc, r"generated_charts\system_pipeline.png", 
            "Figure 3.5.1: End-to-End Operational Execution Pipeline", width=Inches(5.8))
    
    add_body(doc, "The operational execution pipeline progresses through six coordinated stages:")
    
    add_bullet(doc, "Stage 1: Atmospheric Ingestion & Spatial Preprocessing", 
               "Validates incoming sensor and reanalysis streams, imputes missing telemetry, normalizes features via robust scaling, and binds weather vectors to the 200 GCC ward polygons.")
    
    add_bullet(doc, "Stage 2: Rainfall Hazard Classification", 
               "Executes the GBDT classifier, generating the city-wide rainfall alert level (Normal, Elevated, Severe, Catastrophic) and flagging high-risk zones.")
    
    add_bullet(doc, "Stage 3: Multi-Commodity Demand Forecasting", 
               "Computes granular demand estimates for all 200 wards across three vital relief commodities, evaluating baseline demographic requirements and disaster severity multipliers.")
    
    add_bullet(doc, "Stage 4: Conformal Uncertainty Bounds Generation", 
               "Computes nonconformity quantiles, wrapping deterministic demand predictions with 90% upper-bound buffers to ensure zero supply starvation under peak crisis conditions.")
    
    add_bullet(doc, "Stage 5: Multi-Commodity OR-Tools LP Supply Allocation", 
               "Solves the global resource optimization problem across 5 depots and 12 shelters in under 65 milliseconds, outputting exact vehicle load manifests and shelter delivery schedules.")
    
    add_bullet(doc, "Stage 6: Hazard-Aware Routing & Multilingual Dispatch", 
               "Calculates safe navigation routes avoiding submerged streets, coordinates multi-modal vehicle allocations, and dispatches automated Tamil and English emergency advisories.")
    
    doc.add_page_break()
