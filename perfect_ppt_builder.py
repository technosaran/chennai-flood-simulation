import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE_TYPE
import os

TEMPLATE_PATH = r"sample document\AIML B20 -MindBridge- A Multimodal AI Framework for Mental Health Risk Prediction and Personalized Wellness Intervention- FINAL Review_Presentation.pptx"
OUTPUT_DIR = r"c:\Users\saran\Desktop\project X\project document"
FINAL_FILENAME = "C24 - AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform.pptx"

COLOR_TITLE = RGBColor(0x1E, 0x3A, 0x8A)      # Deep Navy Blue
COLOR_HEADING = RGBColor(0x1F, 0x38, 0x64)    # Classic Template Navy
COLOR_BODY = RGBColor(0x1E, 0x29, 0x3B)       # Dark Slate Charcoal
COLOR_HIGHLIGHT = RGBColor(0x04, 0x78, 0x57)  # Professional Emerald Green
COLOR_ACCENT = RGBColor(0x99, 0x1B, 0x1B)     # Alert Brick Red

prs = pptx.Presentation(TEMPLATE_PATH)

def clean_slide_shapes(slide, is_title_slide=False):
    """Remove unwanted floating shapes or old images."""
    to_delete = []
    for s in list(slide.shapes):
        # Keep logos on title slide
        if is_title_slide:
            if s.name in ['Picture 5', 'Picture 3', 'Title 1', 'Subtitle 2', 'TextBox 14']:
                continue
            to_delete.append(s._element)
        else:
            # On other slides, remove any pictures
            if hasattr(s, 'image'):
                to_delete.append(s._element)
            # Remove empty unneeded placeholders
            elif s.has_text_frame and s != slide.shapes.title and not s.text_frame.text.strip():
                to_delete.append(s._element)
    for el in to_delete:
        el.getparent().remove(el)

def set_slide_header(slide, title_text):
    """Set uniform title styling across all slides."""
    title_shape = slide.shapes.title
    if not title_shape:
        for s in slide.shapes:
            if s.has_text_frame and s.top < Inches(1.5):
                title_shape = s
                break
    if not title_shape:
        # Create title shape if missing
        title_shape = slide.shapes.add_textbox(Inches(0.9), Inches(0.4), Inches(11.5), Inches(0.9))
        
    title_shape.left = Inches(0.9)
    title_shape.top = Inches(0.4)
    title_shape.width = Inches(11.5)
    title_shape.height = Inches(0.9)
    tf = title_shape.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = 'Calibri'
    p.font.bold = True
    p.font.size = Pt(32)
    p.font.color.rgb = COLOR_TITLE
    p.alignment = PP_ALIGN.LEFT

def format_footer(slide, slide_num=None, date_str="22 - 10 - 2026"):
    """Ensure footer has consistent slide number and date."""
    for s in slide.shapes:
        if s.has_text_frame:
            for p in s.text_frame.paragraphs:
                # Update date text box
                if any(k in p.text for k in ["08 - 2026", "MM - YYYY", "10 - 2026", "DD"]):
                    p.text = date_str
                    p.font.name = 'Calibri'
                    p.font.size = Pt(11)
                    p.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
                # Update slide number if specified
                elif slide_num is not None and "Footer" in s.name:
                    p.text = str(slide_num)
                    p.font.name = 'Calibri'
                    p.font.size = Pt(12)
                    p.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

print("Starting clean build with perfect consistency...")

# ==========================================
# SLIDE 1: TITLE SLIDE
# ==========================================
s1 = prs.slides[0]
clean_slide_shapes(s1, is_title_slide=True)

if s1.shapes.title:
    s1.shapes.title.left = Inches(0.9)
    s1.shapes.title.top = Inches(2.1)
    s1.shapes.title.width = Inches(11.5)
    s1.shapes.title.height = Inches(0.9)
    tf = s1.shapes.title.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    p.text = "END SEMESTER PROJECT PHASE I - REVIEW"
    p.font.name = 'Calibri'
    p.font.bold = True
    p.font.size = Pt(30)
    p.font.color.rgb = COLOR_TITLE
    p.alignment = PP_ALIGN.CENTER

for s in s1.shapes:
    if s.name == 'Subtitle 2':
        s.left = Inches(1.8)
        s.top = Inches(3.2)
        s.width = Inches(9.8)
        s.height = Inches(3.0)
        tf = s.text_frame
        tf.word_wrap = True
        tf.clear()
        
        lines = [
            ("Project Title: AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform", True, 18, COLOR_HEADING),
            ("", False, 6, None),
            ("Batch Number: AIML C24", True, 16, RGBColor(0x1E, 0x40, 0xAF)),
            ("Guide Name: Mrs. UDHAYA J.M., M.E., Assistant Professor, Dept of AIML", True, 15, COLOR_BODY),
            ("", False, 6, None),
            ("Team Members:", True, 15, COLOR_HEADING),
            ("  • SAJITH AR  (Reg No: 211423247183)", False, 14.5, COLOR_BODY),
            ("  • SARAN R   (Reg No: 211423247189)", False, 14.5, COLOR_BODY),
        ]
        for idx, (t, bold, sz, col) in enumerate(lines):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = t
            p.font.name = 'Calibri'
            p.font.bold = bold
            p.font.size = Pt(sz)
            if col:
                p.font.color.rgb = col
            p.space_after = Pt(2)
format_footer(s1)

# Helper for standard 1-column slides (slides 2, 3, 6, 7, 8, 9, 11, 15, 17, 22, 23, 24)
def build_single_column_slide(slide, slide_num, title, items):
    clean_slide_shapes(slide)
    set_slide_header(slide, title)
    
    # Content shape
    content_shape = None
    for s in slide.shapes:
        if s.has_text_frame and s != slide.shapes.title and "Footer" not in s.name and "TextBox" not in s.name:
            content_shape = s
            break
            
    if content_shape:
        content_shape.left = Inches(0.9)
        content_shape.top = Inches(1.5)
        content_shape.width = Inches(11.5)
        content_shape.height = Inches(4.7)
        tf = content_shape.text_frame
        tf.word_wrap = True
        tf.clear()
        
        for idx, (head, desc, is_alert) in enumerate(items):
            p_head = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p_head.text = head
            p_head.font.name = 'Calibri'
            p_head.font.bold = True
            p_head.font.size = Pt(16)
            p_head.font.color.rgb = COLOR_ACCENT if is_alert else COLOR_HEADING
            p_head.space_before = Pt(6) if idx > 0 else Pt(0)
            p_head.space_after = Pt(2)
            
            if desc:
                p_desc = tf.add_paragraph()
                p_desc.text = desc
                p_desc.font.name = 'Calibri'
                p_desc.font.bold = False
                p_desc.font.size = Pt(14)
                p_desc.font.color.rgb = COLOR_BODY
                p_desc.space_after = Pt(4)
                
    format_footer(slide, slide_num)

# Helper for 2-column slides (slides 12, 13, 14, 16, 18, 19, 20, 21)
def build_two_column_slide(slide, slide_num, title, bullets, image_path, img_w=5.8, img_h=4.5):
    clean_slide_shapes(slide)
    set_slide_header(slide, title)
    
    # Left text shape
    content_shapes = [s for s in slide.shapes if s.has_text_frame and s != slide.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
    if content_shapes:
        left_shape = content_shapes[0]
        left_shape.left = Inches(0.9)
        left_shape.top = Inches(1.5)
        left_shape.width = Inches(5.6)
        left_shape.height = Inches(4.7)
        tf = left_shape.text_frame
        tf.word_wrap = True
        tf.clear()
        
        for idx, (b_head, b_desc) in enumerate(bullets):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.font.name = 'Calibri'
            p.space_after = Pt(8)
            
            # Format head as bold with bullet, desc as normal
            r1 = p.add_run()
            r1.text = "• " + b_head + (" " if b_desc else "")
            r1.font.name = 'Calibri'
            r1.font.bold = True
            r1.font.size = Pt(14.5)
            r1.font.color.rgb = COLOR_HEADING
            
            if b_desc:
                r2 = p.add_run()
                r2.text = b_desc
                r2.font.name = 'Calibri'
                r2.font.bold = False
                r2.font.size = Pt(13.5)
                r2.font.color.rgb = COLOR_BODY
                    
    # Right Image
    if image_path and os.path.exists(image_path):
        slide.shapes.add_picture(image_path, Inches(6.8), Inches(1.5), Inches(img_w), Inches(img_h))
        
    format_footer(slide, slide_num)

# ==========================================
# SLIDE 2: ABSTRACT
# ==========================================
s2 = prs.slides[1]
s2_items = [
    ("Chennai Flood Lab — Unified Crisis Simulation Platform",
     "During severe urban flooding events, rapid and equitable emergency resource distribution is vital to saving lives. Traditional disaster response relies on delayed field surveys, manual spreadsheet accounting, and static routing maps that ignore dynamic road submersions, leading to critical supply stockouts and vehicle stranding.", False),
    ("Dual Predictive Machine Learning Architecture",
     "This platform couples two AI pipelines: a 180-tree Gradient Boosted Decision Tree (GBDT) model trained on 9,131 daily NASA POWER reanalysis records predicting next-day elevated rainfall (>=10 mm/day, 87.12% ROC-AUC), and a 128-tree Extra Trees + Ridge regression blend predicting per-capita emergency drinking water, food, and medical kit demand with up to 96.6% error reduction over heuristic rules.", False),
    ("Conformal Uncertainty & Prescriptive Routing",
     "Split-conformal calibration guarantees finite-sample 90% confidence intervals for relief demand. NetworkX dynamically evaluates road network accessibility against water depth (0.50m evacuation, 0.30m logistics cutoff), while Google OR-Tools solves capacity-constrained shelter allocation and multi-commodity depot logistics. A high-performance Next.js 14 / Leaflet dashboard enables sub-second (<0.45s) interactive scenario simulation, playback, and offline GCC ward exploration.", False)
]
build_single_column_slide(s2, 1, "Abstract", s2_items)

# ==========================================
# SLIDE 3: MOTIVATION
# ==========================================
s3 = prs.slides[2]
s3_items = [
    ("Increasing Severity of Urban Deluges",
     "Rapid urbanization and convective weather shifts have intensified extreme rainfall events across coastal metros like Chennai (2015 floods, 2023 Cyclone Michaung), completely overwhelming conventional municipal emergency infrastructure.", False),
    ("The Critical 'Reactive' Supply Chain Flaw",
     "Relief agencies historically dispatch emergency cargo only after local shortages are reported in panic calls, resulting in life-threatening delays in heavily inundated sectors.", False),
    ("Dynamic Infrastructure Volatility",
     "Surface roads and arterial bridges submerge unevenly during active monsoons. Standard navigation tools lack real-time hydrological depth awareness, leading to stranded rescue convoys.", False),
    ("Dispatcher Cognitive Overload in Resource Deficits",
     "In acute scarcity, human coordinators face high cognitive strain balancing population density, medical urgency, and geographic isolation across 200 GCC wards without mathematical optimization.", False),
    ("Why Existing Systems Fall Short",
     "Standalone flood engines lack logistics coupling, while logistics algorithms assume fully accessible transit networks. An integrated, uncertainty-aware framework is urgently needed.", True)
]
build_single_column_slide(s3, 2, "Motivation", s3_items)

# ==========================================
# SLIDE 4: LITERATURE SURVEY 1
# ==========================================
s4 = prs.slides[3]
clean_slide_shapes(s4)
set_slide_header(s4, "Literature Survey")
s4.shapes.add_picture("generated_charts/lit_survey_1.png", Inches(0.8), Inches(1.4), Inches(11.7), Inches(4.7))
format_footer(s4, 3)

# ==========================================
# SLIDE 5: LITERATURE SURVEY 2
# ==========================================
s5 = prs.slides[4]
clean_slide_shapes(s5)
set_slide_header(s5, "Literature Survey (Cont.)")
s5.shapes.add_picture("generated_charts/lit_survey_2.png", Inches(0.8), Inches(1.4), Inches(11.7), Inches(4.7))
format_footer(s5, 4)

# ==========================================
# SLIDE 6: DISADVANTAGES OF EXISTING SYSTEM
# ==========================================
s6 = prs.slides[5]
s6_items = [
    ("Manual Data Processing Bottlenecks",
     "Relying on human dispatchers to manually log damage reports and update spreadsheets causes critical multi-hour lags during fast-moving flood surges.", True),
    ("Purely Reactive Inventory Tracking",
     "Existing emergency platforms track static depot inventory and only alert coordinators after shortages occur, precluding proactive supply pre-positioning.", True),
    ("Suboptimal & Biased Resource Allocation",
     "When critical supplies are scarce, manual distribution fails to mathematically optimize priority coverage across shelters, resulting in severe regional inequities.", True),
    ("Static GIS Mapping & Ignored Road Submersion",
     "Standard navigation tools assume roads are passable until user accidents occur, leading delivery trucks into submerged arterial bottlenecks (>=0.30m depth).", True),
    ("Isolated Monolithic Systems & Lack of Uncertainty Bounds",
     "Point-prediction ML tools fail to provide confidence intervals, leaving emergency planners without statistical safety buffers for worst-case surges.", True)
]
build_single_column_slide(s6, 5, "Disadvantages of Existing System", s6_items)

# ==========================================
# SLIDE 7: PROPOSED SYSTEM
# ==========================================
s7 = prs.slides[6]
s7_items = [
    ("Spatio-Temporal Inundation Dynamics",
     "Simulates continuous flood spread and water depth decay across discrete time steps (t=0..T) with depth thresholds (0.50m evacuation, 0.30m logistics).", False),
    ("Dual Predictive AI Engine",
     "A 180-tree GBDT model predicts next-day heavy rainfall from NASA POWER reanalysis (87.12% AUC), and a 128-tree Extra Trees/Ridge ensemble predicts per-person relief demands.", False),
    ("Split-Conformal Uncertainty Calibration",
     "Distribution-free finite-sample conformal calibration generates verified 90% confidence intervals for water, food, and medical kit demand.", False),
    ("Mathematical Linear Programming Allocation",
     "Google OR-Tools GLOP optimizer guarantees equitable, capacity-constrained shelter assignments and depot stock conservation with transaction rollback.", False),
    ("Dynamic Flood-Avoidance Routing & Dedicated Fleet Dispatch",
     "NetworkX dynamically updates Chennai OSM road graph weights, calculating safe A*/Dijkstra paths and coordinating dedicated truck, boat, and airlift fleets.", False),
    ("Full-Stack Next.js 14 Interactive Dashboard",
     "Enables real-time scenario simulation (<0.45s), timeline playback, bilingual Tamil/English bulletins, 200-ward GCC atlas, and HTML report export.", False)
]
build_single_column_slide(s7, 6, "Proposed System", s7_items)

# ==========================================
# SLIDE 8: GOAL & KEY OBJECTIVES
# ==========================================
s8 = prs.slides[7]
s8_items = [
    ("Primary Goal",
     "To design, develop, and evaluate an autonomous full-stack crisis simulation and resource optimization platform that couples predictive machine learning, conformal uncertainty quantification, and dynamic network routing for resilient flood response.", False),
    ("Meteorological Hazard Classification (Objective 1)",
     "Train and evaluate a 180-Tree GBDT weather model on 9,131 days of NASA POWER data (Achieved: 87.12% ROC-AUC, 80.36% Recall).", False),
    ("Predictive Demand Modeling & Uncertainty (Objective 2 & 3)",
     "Build a 128-Tree Extra Trees + Ridge ensemble reducing relief demand MAE by 88.1% to 96.6% over rule baselines, backed by verified 90% split-conformal coverage.", False),
    ("Dynamic Inundation Routing & Optimization (Objective 4 & 5)",
     "Dynamically screen Chennai OSM road graph in NetworkX (evacuation cutoff 0.50m, truck cutoff 0.30m) and deploy Google OR-Tools GLOP for equitable allocation.", False),
    ("Live Interactive Demonstration Metric",
     "Success Metric: Examiner can interact live with the dashboard—draw flood polygons or select presets—and view verified routing, shelter allocation, and demand intervals in <0.45 seconds.", True)
]
build_single_column_slide(s8, 7, "Goal & Key Objectives", s8_items)

# ==========================================
# SLIDE 9: ARCHITECTURAL DIAGRAM (OVERVIEW)
# ==========================================
s9 = prs.slides[8]
s9_items = [
    ("Layer 1 & 2 — Input & Spatial Data Ingestion",
     "Interactive flood polygon drawing, circle radius (500–5000m), disaster presets (Velachery, Adyar, Mudichur, T. Nagar), bundled 200 GCC Wards, OSM arterial road graph, 12 shelters, and 5 depots.", False),
    ("Layer 3 & 4 — Inundation Dynamics & Graph Screening",
     "Computes continuous flood spread and water depth decay across time steps t=0..T; dynamically calculates edge impedance and severs impassable corridors in NetworkX (0.50m evacuation, 0.30m trucks).", False),
    ("Layer 5 & 6 — Dual Predictive AI & Optimization",
     "NASA POWER 180-tree rainfall classifier + 128-tree Extra Trees/Ridge demand forecaster, nominal 90% conformal intervals, and Google OR-Tools GLOP capacity-constrained optimization.", False),
    ("Layer 7 — Full-Stack Command Center & Fleet Routing",
     "Safe evacuation shortest paths, dedicated rescue fleet dispatch (trucks, boats, helicopters), bilingual Tamil/English alerts, and Next.js Leaflet dashboard.", False),
    ("Key Design Insight",
     "Combining predictive weather classification with dynamic graph impedance and mathematical resource optimization provides guaranteed stock conservation and flood-free transit.", True)
]
build_single_column_slide(s9, 8, "Architectural Diagram", s9_items)

# ==========================================
# SLIDE 10: ARCHITECTURAL FLOWCHART (IMAGE)
# ==========================================
s10 = prs.slides[9]
clean_slide_shapes(s10)
set_slide_header(s10, "System Architecture Flowchart")
s10.shapes.add_picture("generated_charts/architecture_flow.png", Inches(2.9), Inches(1.3), Inches(7.3), Inches(5.1))
format_footer(s10, 9)

# ==========================================
# SLIDE 11: MODULES EXPLANATION
# ==========================================
s11 = prs.slides[10]
s11_items = [
    ("Module 1 — Data & Scenario Ingestion",
     "Validates incident parameters (rainfall intensity 1–5, water depth 0.1–3.0m, spread rate) and spatial inputs across 200 GCC wards and OSM road networks.", False),
    ("Module 2 — Inundation Dynamics & Graph Pruning",
     "Calculates temporal flood dilation and depth decay. Dynamically prunes NetworkX road graph edges exceeding safe transit depths (0.50m evacuation, 0.30m trucks).", False),
    ("Module 3 — Dual Predictive ML Engine",
     "NASA POWER 180-tree GBDT model classifies next-day rainfall hazard (>=10mm, 87.12% AUC). 128-Tree Extra Trees + Ridge ensemble predicts per-capita water, food, and medical demand.", False),
    ("Module 4 — Split-Conformal Calibration",
     "Computes finite-sample non-conformity scores on dedicated calibration data, producing distribution-free 90% prediction intervals with humanitarian minimum safety floors.", False),
    ("Module 5 — Mathematical Optimization (OR-Tools)",
     "Formulates multi-commodity distribution as a Linear Program (GLOP), enforcing shelter capacities, depot stock bounds, and transaction rollback.", False),
    ("Module 6 — Dynamic Routing & Multi-Modal Fleet",
     "Solves shortest-path Dijkstra/A* routing for evacuation and dispatches configured rescue trucks, flood-rescue boats, and airlift units to isolated ward clusters.", False)
]
build_single_column_slide(s11, 10, "Modules: Explanation of Architectural Diagram", s11_items)

# ==========================================
# SLIDE 12: DATASET STATISTICS
# ==========================================
s12 = prs.slides[11]
s12_bullets = [
    ("NASA POWER Chennai Weather Dataset:", "9,131 daily records (2001-2025) at latitude 13.0827, longitude 80.2707."),
    ("Meteorological Attributes (13 Features):", "Precipitation, temp, humidity, wind, pressure, 3/7-day lags, and cyclic seasonality."),
    ("Strict Chronological Split Protocol:", "Training: 6,567 days (2001-2018) | Val: 1,096 days (2019-2021) | Test: 1,461 days (2022-2025)."),
    ("Multi-Scenario Relief Demand Dataset:", "55,000 synthetic disaster rows; complete hold-out of 2023 Cyclone Michaung (16,513 rows)."),
    ("Spatial Infrastructure Inventory:", "12 verified public shelters (5,400 capacity), 5 depots, 10 distribution hubs, 200 wards.")
]
build_two_column_slide(s12, 11, "DATASET STATISTICS", s12_bullets, "generated_charts/dataset_statistics_table.png", img_w=5.7, img_h=4.5)

# ==========================================
# SLIDE 13: MODEL EVALUATION
# ==========================================
s13 = prs.slides[12]
s13_bullets = [
    ("Multi-Model Comparative Framework:", "Evaluated Gradient Boosted Trees (180 depth-2 trees, lr=0.04), Random Forest (300 estimators), and Persistence baselines for weather."),
    ("Multi-Output Relief Demand Ensemble:", "64 Extra Trees, 64 Random Forest, and Scaled Ridge Regression with convex out-of-event weight grid optimization."),
    ("Strict Held-Out Evaluation:", "Zero-leakage testing on chronological 2022-2025 weather reanalysis and Cyclone Michaung disaster group."),
    ("Superior Life-Safety Metrics:", "Selected Gradient Boosted model achieved 0.8712 ROC-AUC and 80.36% Recall, prioritizing emergency warning responsiveness.")
]
build_two_column_slide(s13, 12, "MODEL EVALUATION", s13_bullets, "generated_charts/model_performance_comparison.png", img_w=5.8, img_h=4.5)

# ==========================================
# SLIDE 14: CONFIDENCE CALIBRATION & UNCERTAINTY
# ==========================================
s14 = prs.slides[13]
s14_bullets = [
    ("Split-Conformal Prediction Framework:", "Employs distribution-free inductive conformal prediction on 9,622 independent calibration rows."),
    ("Finite-Sample Mathematical Coverage:", "Achieves nominal 90% marginal coverage on held-out test data (Water: 89.81%, Food: 90.29%, Medical Kits: 93.90%)."),
    ("Reliable Emergency Safety Margins:", "Automatically bounds demand upper and lower estimates to prevent supply deficits under extreme surges."),
    ("Humanitarian Planning Minimums:", "Enforces strict safety floors (3.0 L drinking water, 3.0 food units, 0.02 medical kits per capita) to prevent degenerate allocations.")
]
build_two_column_slide(s14, 13, "CONFIDENCE CALIBRATION AND EXPLAINABILITY", s14_bullets, "generated_charts/confidence_calibration.png", img_w=5.8, img_h=4.5)

# ==========================================
# SLIDE 15: WHY GRADIENT BOOSTING & EXTRA TREES?
# ==========================================
s15 = prs.slides[14]
s15_items = [
    ("Tabular Data Superiority",
     "Meteorological variables and disaster relief factors are structured tabular matrices where shallow tree ensembles consistently outperform deep networks without overfitting.", False),
    ("Pure-Python Zero-Dependency Inference",
     "Deployed models are exported as lightweight JSON decision trees and linear coefficients, executing in <1.2 ms with standard Python dictionaries—no PyTorch or GPU required.", False),
    ("Asymmetric Recall Optimization",
     "Shallow depth-2 gradient boosting with validation-tuned decision thresholds achieves 80.36% recall, critically minimizing missed disaster warnings.", False),
    ("Robust Out-of-Event Generalization",
     "Blending Extra Trees with Ridge regression dampens variance across extreme out-of-event disaster scenarios.", False),
    ("Provenance & Auditability",
     "SHA-256 fingerprinting for datasets and model weights guarantees exact auditability and zero drift during panel evaluation.", False)
]
build_single_column_slide(s15, 14, "WHY GRADIENT BOOSTING & EXTRA TREES?", s15_items)

# ==========================================
# SLIDE 16: SYSTEM ARCHITECTURE OVERVIEW
# ==========================================
s16 = prs.slides[15]
s16_bullets = [
    ("Input Layer:", "13 NASA atmospheric features + Chennai 200 GCC wards and OSM road network."),
    ("Inundation Dynamics Engine:", "Geometric flood spread with depth-dependent road screening (0.50m evacuation, 0.30m logistics)."),
    ("Dual Machine Learning Inference:", "180-Tree GBDT weather classifier + 128-Tree Extra Trees/Ridge demand ensemble."),
    ("Conformal Uncertainty Calibration:", "Split-conformal 90% confidence intervals with planning floors."),
    ("Mathematical Optimization:", "Google OR-Tools GLOP solver for capacity-constrained allocation."),
    ("Output & Operational Visualization:", "Flood-avoidant evacuation routes, fleet dispatch plans, and interactive GIS visualization.")
]
build_two_column_slide(s16, 15, "System Architecture Overview", s16_bullets, "generated_charts/system_pipeline.png", img_w=5.7, img_h=4.5)

# ==========================================
# SLIDE 17: ARCHITECTURE FLOW / PIPELINE
# ==========================================
s17 = prs.slides[16]
s17_items = [
    ("1. Dataset Ingestion", "NASA POWER 9,131 daily records, GCC 200 wards, OSM Chennai road network.", False),
    ("2. Hydrological Simulation", "Dynamic flood polygon dilation and depth decay across time steps t=0..T.", False),
    ("3. Road Graph Pruning", "NetworkX screens road segments; closes routes with depth >= 0.50m (evacuation) or >= 0.30m (trucks).", False),
    ("4. Shelter Accessibility Screening", "Identifies safe, non-inundated public shelters from 12 verified municipal locations.", False),
    ("5. Machine Learning Demand Prediction", "128-Tree Extra Trees + Ridge ensemble infers per-person resource needs.", False),
    ("6. Split-Conformal Interval Calculation", "Generates verified 90% upper and lower demand confidence bounds.", False),
    ("7. Mathematical Resource Allocation", "Google OR-Tools GLOP solver optimizes relief dispatch under inventory conservation.", False),
    ("8. Dynamic Evacuation & Multi-Modal Routing", "A* shortest path finds safe corridors; identifies stranded populations for boat/airlift dispatch.", False),
    ("9. Interactive Dashboard & Report Generation", "Next.js GIS UI visualizes results in <0.45s and exports self-contained HTML reports.", False)
]
build_single_column_slide(s17, 16, "Architecture Flow & Pipeline Execution", s17_items)

# ==========================================
# SLIDE 18: BASELINE COMPARISON
# ==========================================
s18 = prs.slides[17]
s18_bullets = [
    ("Drinking Water Demand:", "Rule MAE 3,647.53 L vs Proposed ML 122.44 L (96.6% Error Reduction)."),
    ("Food Rations Demand:", "Rule MAE 1,843.65 vs Proposed ML 92.69 units (95.0% Error Reduction)."),
    ("Medical Kits Demand:", "Rule MAE 91.54 vs Proposed ML 10.90 kits (88.1% Error Reduction)."),
    ("Weather Hazard ROC-AUC:", "Proposed GBDT: 0.8712 AUC vs Persistence: 0.7138 AUC vs Baseline: 0.5000 AUC."),
    ("Weather Hazard Recall:", "Proposed GBDT: 80.36% vs Persistence: 49.40% vs Baseline: 0.00%."),
    ("Key Observation:", "Proposed ML achieves dramatic error reduction across all metrics while prioritizing life safety.")
]
build_two_column_slide(s18, 17, "Baseline Comparison", s18_bullets, "generated_charts/baseline_comparison.png", img_w=5.8, img_h=4.5)

# ==========================================
# SLIDE 19: TRAINING DYNAMICS
# ==========================================
s19 = prs.slides[18]
s19_bullets = [
    ("Cross-Validation Protocol:", "5-fold stratified cross-validation evaluated model stability across chronological and event-based data splits."),
    ("Consistent Fold Discrimination:", "Gradient Boosted weather model achieved consistent ROC-AUC across all five partitions."),
    ("Fold-Wise ROC-AUC Scores:", "Fold 1: 0.862 | Fold 2: 0.884 | Fold 3: 0.871 | Fold 4: 0.855 | Fold 5: 0.884."),
    ("Summary Statistics:", "Mean ROC-AUC: 0.871 +/- 0.012 with no fold scoring below 0.85."),
    ("GroupKFold Generalization:", "Relief demand models verified generalization across distinct historical flood profiles without data leakage.")
]
build_two_column_slide(s19, 18, "Training Dynamics: 5-Fold Cross-Validation", s19_bullets, "generated_charts/cross_validation_roc.png", img_w=5.8, img_h=4.5)

# ==========================================
# SLIDE 20: PREDICTION ACCURACY
# ==========================================
s20 = prs.slides[19]
s20_bullets = [
    ("ROC-AUC Score:", "87.12% on held-out test data (2022-2025)."),
    ("Balanced Accuracy:", "78.62% across imbalanced rainfall classes."),
    ("Sensitivity / Recall:", "80.36% (Correctly detected 135 of 168 elevated rainfall days)."),
    ("Raw Test Accuracy:", "77.28% on chronological test partition."),
    ("Precision:", "31.11% (Reflects conservative, safety-first thresholding)."),
    ("F1-Score:", "44.85% (Substantial improvement over zero baseline)."),
    ("Operational Summary:", "The model demonstrates strong discriminative capability for early flood warning with minimal missed alarms.")
]
build_two_column_slide(s20, 19, "Prediction Accuracy", s20_bullets, "generated_charts/prediction_accuracy.png", img_w=5.8, img_h=4.5)

# ==========================================
# SLIDE 21: GRAPH INSIGHTS & CONFUSION MATRIX
# ==========================================
s21 = prs.slides[20]
s21_bullets = [
    ("Figure 1 (Model Benchmark):", "GBDT dominates persistence in Recall (80.4% vs 49.4%) and ROC-AUC (0.871 vs 0.714)."),
    ("Figure 2 (Confusion Matrix):", "994 true negatives, 135 true positives, and only 33 false negatives over 4 test years."),
    ("Life-Safety Priority:", "The 80.4% recall ensures timely disaster mobilization with minimal missed hazardous events."),
    ("Feature Importance Drivers:", "Preceding 7-day cumulative precipitation and relative humidity were identified as primary predictors."),
    ("Conformal Interval Stability:", "Uncertainty intervals maintain narrow, usable bounds across diverse scenario severities.")
]
build_two_column_slide(s21, 20, "Graph Insights & Confusion Matrix Analysis", s21_bullets, "generated_charts/confusion_matrix.png", img_w=5.2, img_h=4.5)

# ==========================================
# SLIDE 22: DISCUSSION
# ==========================================
s22 = prs.slides[21]
s22_items = [
    ("Integrated Cross-Domain Architecture",
     "Bridges atmospheric reanalysis, spatio-temporal inundation dynamics, operations research, and graph algorithms into a unified platform.", False),
    ("Life-Safety First Optimization",
     "Calibrating models for high recall (80.4%) and providing conformal 90% upper bounds prevents shelter supply shortages during extreme rainfall surges.", False),
    ("Provable Stock Conservation",
     "Google OR-Tools GLOP solver ensures allocations never exceed depot inventory; atomic transaction rollback prevents corrupted ledger states on network disruptions.", False),
    ("Sub-Second Real-Time Responsiveness",
     "Pure-Python graph algorithms and lightweight JSON tree traversal compute complete multi-step simulations in <0.45s, facilitating live interactive examiner demonstrations.", False),
    ("Transparent Scientific Boundaries",
     "Explicitly acknowledges synthetic demand labels and simplified road geometry while establishing a reproducible foundation for future hydraulic coupling.", False)
]
build_single_column_slide(s22, 21, "Discussion", s22_items)

# ==========================================
# SLIDE 23: CONCLUSION
# ==========================================
s23 = prs.slides[22]
s23_items = [
    ("High-Performance Hazard Prediction",
     "Developed and verified a 180-tree GBDT model achieving 87.12% ROC-AUC and 80.36% recall on 4 years of untouched NASA weather reanalysis.", False),
    ("Significant Relief Error Reduction",
     "Extra Trees + Ridge ensemble reduces demand prediction MAE by 88.1% to 96.6% compared to traditional planning rules, backed by nominal 90% conformal intervals.", False),
    ("Dynamic Flood-Avoidant Routing",
     "Implemented dynamic NetworkX graph routing that automatically isolates submerged corridors (>=0.30m trucks, >=0.50m pedestrians) and coordinates multi-modal rescue fleets.", False),
    ("Mathematically Optimal Allocation",
     "Google OR-Tools GLOP solver guarantees equitable, capacity-compliant shelter and supply distribution with strict stock conservation.", False),
    ("Full-Stack Operational Platform",
     "Built an interactive Next.js 14 / FastAPI application featuring a 200-ward GCC atlas, bilingual Tamil/English bulletins, timeline playback, and reproducible exports.", False)
]
build_single_column_slide(s23, 22, "Conclusion", s23_items)

# ==========================================
# SLIDE 24: FUTURE WORK
# ==========================================
s24 = prs.slides[23]
s24_items = [
    ("Hydrodynamic PDE Integration",
     "Couple 2D shallow water equation solvers (LISFLOOD-FP / SWMM) with high-resolution LiDAR Digital Elevation Models for physics-based flood routing.", False),
    ("Real-Time IoT Telemetry",
     "Integrate live ultrasonic water-level sensors and automatic rain gauges across Adyar and Cooum river basins for continuous automated data feeds.", False),
    ("Vehicle Routing with Time Windows (VRPTW)",
     "Expand OR-Tools logistics to solve multi-vehicle routing with fleet battery/fuel limits, driver shift constraints, and dynamic pickup requests.", False),
    ("Offline Mobile Edge Deployment",
     "Package the lightweight JSON inference runtime into Progressive Web Apps (PWA) and Android offline APKs for frontline disaster responders.", False),
    ("Empirical Field Validation",
     "Partner with Tamil Nadu Disaster Management Authority (TNDMA) for real-world validation against observed flood logistics records.", False)
]
build_single_column_slide(s24, 23, "Future Work", s24_items)

# ==========================================
# SLIDE 25: THANK YOU
# ==========================================
s25 = prs.slides[24]
clean_slide_shapes(s25)
if s25.shapes.title:
    s25.shapes.title.left = Inches(1.5)
    s25.shapes.title.top = Inches(2.2)
    s25.shapes.title.width = Inches(10.3)
    s25.shapes.title.height = Inches(1.5)
    tf = s25.shapes.title.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    p.text = "Thank You !!!"
    p.font.name = 'Calibri'
    p.font.bold = True
    p.font.size = Pt(44)
    p.font.color.rgb = COLOR_TITLE
    p.alignment = PP_ALIGN.CENTER
    
    p2 = tf.add_paragraph()
    p2.text = "AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform"
    p2.font.name = 'Calibri'
    p2.font.bold = True
    p2.font.size = Pt(18)
    p2.font.color.rgb = COLOR_HEADING
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(12)
    
    p3 = tf.add_paragraph()
    p3.text = "Department of Artificial Intelligence & Machine Learning\nPanimalar Engineering College, Chennai"
    p3.font.name = 'Calibri'
    p3.font.size = Pt(15)
    p3.font.color.rgb = COLOR_BODY
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(6)
format_footer(s25)

# ==========================================
# SLIDE 26: QUERIES?
# ==========================================
s26 = prs.slides[25]
clean_slide_shapes(s26)
if s26.shapes.title:
    s26.shapes.title.left = Inches(1.5)
    s26.shapes.title.top = Inches(2.4)
    s26.shapes.title.width = Inches(10.3)
    s26.shapes.title.height = Inches(1.5)
    tf = s26.shapes.title.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    p.text = "Queries?"
    p.font.name = 'Calibri'
    p.font.bold = True
    p.font.size = Pt(44)
    p.font.color.rgb = COLOR_TITLE
    p.alignment = PP_ALIGN.CENTER
    
    p2 = tf.add_paragraph()
    p2.text = "Open for Technical Discussion & Examination"
    p2.font.name = 'Calibri'
    p2.font.bold = True
    p2.font.size = Pt(18)
    p2.font.color.rgb = COLOR_HEADING
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(12)
format_footer(s26)

# ==========================================
# SAVE THE EXACT SINGLE PRESENTATION
# ==========================================
final_path = os.path.join(OUTPUT_DIR, FINAL_FILENAME)
prs.save(final_path)
print(f"Successfully saved final presentation to: {final_path}")

# Delete any other pptx files in OUTPUT_DIR to satisfy 'only one' requirement
for fname in os.listdir(OUTPUT_DIR):
    if fname.endswith(".pptx") and fname != FINAL_FILENAME:
        fpath = os.path.join(OUTPUT_DIR, fname)
        os.remove(fpath)
        print(f"Removed extra file: {fpath}")

print("Build complete: Exactly ONE best presentation exists in project document!")
