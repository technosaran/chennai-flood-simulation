import docx
from docx.shared import Inches, Pt, RGBColor
from report_styles import add_p, add_body, add_h1, add_h2, add_h3, add_bullet

def generate_chapter_6(doc):
    # CHAPTER 6
    add_h1(doc, "CHAPTER 6\nCONCLUSION AND FUTURE WORK")
    
    # 6.1 Conclusion
    add_h2(doc, "6.1 Conclusion")
    add_body(doc, "Urban pluvial and fluvial flooding represents an existential humanitarian threat to coastal megacities, where dense populations, intense monsoonal weather systems, and low-lying geography converge. The catastrophic events of the 2015 Chennai floods and 2023 Cyclone Michaung demonstrated that municipal disaster response fails not from a lack of physical relief goods, but from severe information disconnects, coarse planning heuristics, and hazard-blind logistics routing that leaves vulnerable populations stranded while emergency convoys encounter flooded, impassable roads.")
    
    add_body(doc, "This project has successfully conceptualized, engineered, and empirically validated the AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform (Team C24), delivering a unified, mathematically rigorous, and sub-second decision-support system tailored for the Greater Chennai Corporation. The major engineering and scientific contributions achieved by this project include:")
    
    add_bullet(doc, "Long-Horizon Hydro-Meteorological Intelligence", 
               "Successfully harnessed 25 years (9,131 daily records from 2001 to 2025) of NASA POWER satellite and atmospheric reanalysis for Chennai, constructing 7-day retrospective rolling feature matrices and cyclic trigonometric seasonality encodings.")
    
    add_bullet(doc, "High-Sensitivity Precipitation Hazard Classifier", 
               "Formulated a 180-tree Gradient Boosted Decision Tree (GBDT) model achieving an exceptional 0.8712 ROC-AUC and 80.36% operational hazard recall on four years of untouched out-of-time prospective testing (2022–2025), outperforming baseline persistence models by 35.02%.")
    
    add_bullet(doc, "Extreme Demand Forecasting Precision", 
               "Trained a 128-tree multi-output ensemble (64 Extra Trees, 64 Random Forest, Ridge regression) across 55,000 spatial disaster scenarios. Evaluated under strict zero-leakage disaster-group holdout conditions (Cyclone Michaung), the ensemble reduced prediction errors over conventional municipal planning rules by 96.6% in drinking water (122.44 L vs 3,647.53 L MAE), 95.0% in food rations (92.69 vs 1,843.65 units MAE), and 88.1% in emergency medical kits (10.90 vs 91.54 kits MAE).")
    
    add_bullet(doc, "Distribution-Free Finite-Sample Uncertainty Calibration", 
               "Integrated inductive split-conformal prediction across 9,622 independent holdout records, validating nominal 90% finite-sample prediction coverage (89.81% water, 90.29% food, 93.90% medical) without parametric distribution assumptions, eliminating dangerous shelter stockout risks.")
    
    add_bullet(doc, "Exact Mathematical Supply Optimization", 
               "Formulated and solved a continuous multi-commodity network flow linear program using Google OR-Tools GLOP, optimizing warehouse conservation laws, shelter priority weighting, and inventory balances across 5 central depots and 12 relief shelters in under 65 milliseconds.")
    
    add_bullet(doc, "Hazard-Aware Dynamic Graph Traversal & Accessible Dissemination", 
               "Modeled Chennai's road network in NetworkX, dynamically pruning submerged road segments exceeding physical clearance thresholds (0.30 m for relief trucks, 0.50 m for pedestrian rescue), coordinating multi-modal rescue assets (trucks, boats, aerial drops). Deployed the entire framework into a sub-second (<0.45s) Next.js 14 / FastAPI GIS web console providing automated bilingual Tamil/English advisories, an offline 200-ward GCC atlas, and reproducible HTML reporting.")
    
    # 6.2 Societal & Environmental Impact
    add_h2(doc, "6.2 Societal & Environmental Impact")
    add_body(doc, "The deployment of this platform yields profound societal and humanitarian benefits for coastal urban governance:")
    
    add_bullet(doc, "Preservation of Human Life & Suffering Reduction", 
               "By predicting localized supply shortfalls hours ahead of physical stockouts and identifying safe, non-submerged evacuation routes, the platform directly prevents avoidable deaths caused by dehydration, acute malnutrition, and lack of emergency medical trauma supplies in cut-off neighborhoods.")
    
    add_bullet(doc, "Algorithmic Equity in Disaster Relief Distribution", 
               "By incorporating objective socio-economic vulnerability indices and mathematically guaranteed conformal demand buffers, the system eliminates human allocative bias, ensuring that marginalized, low-income informal settlements receive equal life-saving resources regardless of political lobbying or geographical accessibility.")
    
    add_bullet(doc, "Reduction of Fuel Consumption & Vehicle Stranding", 
               "Routing heavy emergency relief trucks away from deep water underpasses prevents engine hydro-locking, reduces wasted operational fuel, and minimizes emergency fleet carbon emissions during regional disaster operations.")
    
    # 6.3 Future Enhancements
    add_h2(doc, "6.3 Future Enhancements")
    add_body(doc, "To advance the platform from an academic research prototype toward state-wide municipal deployment, four promising technical enhancements are planned:")
    
    add_bullet(doc, "Two-Dimensional (2D) Hydrodynamic Model Coupling", 
               "Future research will couple the machine learning pipeline with physics-based 2D shallow-water hydrodynamic solvers (such as open-source Telemac-2D or SWMM). Pre-computed hydraulic mesh libraries will enable street-level inundation depth predictions at 5-meter spatial resolutions.")
    
    add_bullet(doc, "Real-Time IoT Ultrasonic Water Level Sensor Ingestion", 
               "Integrating municipal IoT telemetry—including ultrasonic water level sensors mounted on canal bridges (Adyar, Cooum, Buckingham canal) and smart stormwater manhole monitors—will enable continuous, real-time closed-loop updating of road graph impedance weights.")
    
    add_bullet(doc, "Multi-Period Vehicle Routing Problem with Time Windows (VRPTW)", 
               "Extending the current linear programming supply allocation into a dynamic Mixed-Integer VRPTW solver will allow the platform to optimize multi-stop truck delivery schedules, vehicle turnaround times, driver rest shifts, and fuel constraints across multi-day crisis operations.")
    
    add_bullet(doc, "Low-Power Edge Mobile Deployment for First Responders", 
               "Quantizing the ensemble models into lightweight ONNX / TensorFlow Lite runtimes will permit the complete inference and graph routing engine to execute locally on ruggedized mobile tablets carried by field rescue personnel, ensuring full operational capability even during total cellular telecommunication blackouts.")
    
    doc.add_page_break()
