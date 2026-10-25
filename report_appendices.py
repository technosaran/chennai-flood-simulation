import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from report_styles import add_p, add_body, add_h1, add_h2, add_h3, add_bullet, add_fig, add_code_block
import os

def generate_appendices(doc):
    # ==========================================
    # APPENDIX COVER
    # ==========================================
    add_p(doc, "", space_before=150)
    add_p(doc, "APPENDIX", font_size=28, bold=True, align=docx.enum.text.WD_ALIGN_PARAGRAPH.CENTER, space_before=50, space_after=18)
    doc.add_page_break()

    # ==========================================
    # APPENDIX A.1: SUSTAINABLE DEVELOPMENT GOALS
    # ==========================================
    add_h2(doc, "A.1 SUSTAINABLE DEVELOPMENT GOALS (SDGs)")
    
    p_intro = doc.add_paragraph()
    p_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_intro.paragraph_format.space_before = Pt(0)
    p_intro.paragraph_format.space_after = Pt(4)
    p_intro.paragraph_format.line_spacing = 1.2
    r_i = p_intro.add_run("The AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform directly advances five United Nations Sustainable Development Goals (SDGs) by deploying predictive artificial intelligence and equitable disaster relief logistics:")
    r_i.font.name = 'Times New Roman'
    r_i.font.size = Pt(12)
    
    sdg_items = [
        ("1. SDG 11: SUSTAINABLE CITIES AND COMMUNITIES", 
         "Target 11.5 aims to significantly reduce casualties and direct economic losses from water-related disasters. By providing ward-level inundation forecasting and hazard-aware evacuation routing for Chennai's 7.1 million residents, the platform directly enhances urban disaster resilience and protects vulnerable coastal settlements."),
        ("2. SDG 13: CLIMATE ACTION", 
         "Target 13.1 mandates strengthening resilience and adaptive capacity to climate-related hazards. As climate change intensifies monsoonal cloudbursts and Bay of Bengal cyclones, the platform serves as an operational adaptation tool, shifting municipal response from reactive recovery to proactive crisis staging."),
        ("3. SDG 9: INDUSTRY, INNOVATION, AND INFRASTRUCTURE", 
         "Target 9.1 calls for developing resilient, sustainable infrastructure. By coupling predictive machine learning with dynamic road network impedance modeling, the platform prevents arterial transit paralysis, prevents rescue vehicle hydro-locking, and preserves life-saving logistics corridors during severe floods."),
        ("4. SDG 3: GOOD HEALTH AND WELL-BEING", 
         "Target 3.d focuses on early warning and risk reduction for public health. By reducing drinking water demand prediction errors by 96.6% and emergency medical kit errors by 88.1%, the platform prevents post-disaster waterborne epidemics (cholera, leptospirosis) and guarantees immediate trauma care supplies at relief shelters."),
        ("5. SDG 17: PARTNERSHIPS FOR THE GOALS", 
         "Target 17.6 promotes multi-stakeholder knowledge sharing and open-source technological innovation. Leveraging open satellite telemetry (NASA POWER) and open-source frameworks (FastAPI, OR-Tools, Next.js), the platform establishes a reproducible, zero-licensing blueprint deployable across vulnerable coastal cities worldwide.")
    ]
    
    for title, desc in sdg_items:
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.2
        
        r1 = p.add_run(title + ": ")
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11.5)
        r1.font.bold = True
        
        r2 = p.add_run(desc)
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11.5)
        
    doc.add_page_break()

    # ==========================================
    # APPENDIX A.2: SYSTEM SOURCE CODE
    # ==========================================
    add_h2(doc, "A.2 SYSTEM SOURCE CODE LISTINGS")
    add_body(doc, "This section presents clean, production-grade source code listings from the platform's backend implementation, showcasing the machine learning training pipelines, real-time inference services, and mathematical optimization engines.")
    
    # A.2.1 train_weather_model.py
    weather_train_path = r"backend\ml_pipeline\train_weather_model.py"
    if os.path.exists(weather_train_path):
        with open(weather_train_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()]
        add_code_block(doc, "Listing A.2.1: 180-Tree GBDT Weather Hazard Training Pipeline (train_weather_model.py)", lines)
        doc.add_page_break()

    # A.2.2 train_demand_ensemble.py
    demand_train_path = r"backend\ml_pipeline\train_demand_ensemble.py"
    if os.path.exists(demand_train_path):
        with open(demand_train_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()]
        add_code_block(doc, "Listing A.2.2: Multi-Output Demand Ensemble Training & Conformal Calibration (train_demand_ensemble.py)", lines)
        doc.add_page_break()

    # A.2.3 weather_predictor.py
    weather_pred_path = r"backend\app\services\weather_predictor.py"
    if os.path.exists(weather_pred_path):
        with open(weather_pred_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()]
        add_code_block(doc, "Listing A.2.3: Real-Time Weather Inference Service (weather_predictor.py)", lines)
        doc.add_page_break()

    # A.2.4 demand_predictor.py
    demand_pred_path = r"backend\app\services\demand_predictor.py"
    if os.path.exists(demand_pred_path):
        with open(demand_pred_path, "r", encoding="utf-8") as f:
            lines = [line.rstrip() for line in f.readlines()]
        add_code_block(doc, "Listing A.2.4: Split-Conformal Demand Prediction Service (demand_predictor.py)", lines)
        doc.add_page_break()

    # A.2.5 supply_solver.py (Core allocation methods)
    supply_solver_path = r"backend\app\services\supply_solver.py"
    if os.path.exists(supply_solver_path):
        with open(supply_solver_path, "r", encoding="utf-8") as f:
            all_lines = [line.rstrip() for line in f.readlines()]
        # Extract first 150 lines representing core linear programming logic
        core_lines = all_lines[:145]
        core_lines.append("# ... [Full operational wrapper and logging logic omitted for brevity] ...")
        add_code_block(doc, "Listing A.2.5: OR-Tools Multi-Commodity Supply Allocation Engine (supply_solver.py - Core LP Formulation)", core_lines)
        doc.add_page_break()

    # A.2.6 evacuation_solver.py (Core routing methods)
    evac_solver_path = r"backend\app\services\evacuation_solver.py"
    if os.path.exists(evac_solver_path):
        with open(evac_solver_path, "r", encoding="utf-8") as f:
            all_lines = [line.rstrip() for line in f.readlines()]
        core_lines = all_lines[:140]
        core_lines.append("# ... [Multi-modal boat and aerial dispatch dispatch wrappers omitted for brevity] ...")
        add_code_block(doc, "Listing A.2.6: Dynamic Flood-Aware Evacuation Routing Engine (evacuation_solver.py - Core Graph Traversal)", core_lines)
        doc.add_page_break()

    # ==========================================
    # APPENDIX A.3: SYSTEM EXECUTION SCREENSHOTS
    # ==========================================
    add_h2(doc, "A.3 SYSTEM EXECUTION SCREENSHOTS")
    add_body(doc, "This section presents actual high-resolution graphical interface screenshots captured during the operational execution of the platform across desktop, tablet, and mobile displays, arranged two figures per page for comprehensive side-by-side inspection.")
    
    screenshot_pairs = [
        [
            (r"docs\verification\desktop.png", 
             "Figure A.3.1: Full Executive Operations Dashboard with Real-Time Flood Inundation Overlay"),
            (r"docs\feature-tour\route-inspector.png", 
             "Figure A.3.2: Hazard-Aware Evacuation Routing Inspector with Road Submersion Verification")
        ],
        [
            (r"docs\feature-tour\ward-atlas.png", 
             "Figure A.3.3: 200 Greater Chennai Corporation Ward Vulnerability and Logistics Atlas"),
            (r"docs\feature-tour\comparison.png", 
             "Figure A.3.4: Multi-Disaster Scenario Comparison Engine (2015 vs 2023 vs Cyclone Michaung)")
        ],
        [
            (r"docs\feature-tour\weather-replay.png", 
             "Figure A.3.5: Historical Weather Replay & Precipitation Telemetry Ingestion"),
            (r"docs\feature-tour\fleet.png", 
             "Figure A.3.6: Multi-Modal Rescue Fleet Allocator (High-Clearance Trucks, Boats, Aerial Drops)")
        ],
        [
            (r"docs\feature-tour\advice-tamil.png", 
             "Figure A.3.7: Automated Bilingual Tamil/English Disaster Advisory Dispatch Console"),
            (r"docs\verification\mobile_composite.png", 
             "Figure A.3.8: Responsive Mobile Field Dispatch Interface for Municipal First Responders")
        ]
    ]
    
    for p_idx, pair in enumerate(screenshot_pairs):
        max_h = Inches(2.9) if p_idx == 0 else Inches(3.2)
        for img_path, caption in pair:
            add_fig(doc, img_path, caption, width=Inches(5.4), max_h=max_h)
        doc.add_page_break()
