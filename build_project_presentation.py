import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE_TYPE
import os

TEMPLATE_PATH = r"C:\Users\saran\Desktop\AIML B20 -MindBridge- A Multimodal AI Framework for Mental Health Risk Prediction and Personalized Wellness Intervention- FINAL Review_Presentation.pptx"
OUTPUT_DIR = r"c:\Users\saran\Desktop\project X\project document"
PRIMARY_FILENAME = "C24 - AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform.pptx"

os.makedirs(OUTPUT_DIR, exist_ok=True)
prs = pptx.Presentation(TEMPLATE_PATH)

def clear_images_from_slide(slide):
    to_remove = []
    for s in slide.shapes:
        if hasattr(s, 'image') and s.name not in ['Picture 5', 'Picture 3']:
            to_remove.append(s._element)
    for el in to_remove:
        el.getparent().remove(el)

def set_slide_title(slide, title_text):
    if slide.shapes.title:
        slide.shapes.title.text = title_text
        for p in slide.shapes.title.text_frame.paragraphs:
            p.font.name = 'Arial'
            p.font.bold = True
            p.font.size = Pt(24)
            p.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

def update_footer_date(slide, date_str="22 - 10 - 2026"):
    for s in slide.shapes:
        if s.has_text_frame:
            for p in s.text_frame.paragraphs:
                if any(k in p.text for k in ["08 - 2026", "MM - YYYY", "10 - 2026", "MM \u2013 YYYY", "\u2013 2026"]):
                    p.text = date_str
                    p.font.name = 'Arial'
                    p.font.size = Pt(11)

print("Starting slide-by-slide transformation...")

# ==========================================
# SLIDE 1: TITLE SLIDE
# ==========================================
s1 = prs.slides[0]
if s1.shapes.title:
    s1.shapes.title.text = "END SEMESTER PROJECT PHASE I- REVIEW"
    for p in s1.shapes.title.text_frame.paragraphs:
        p.font.name = 'Arial'
        p.font.bold = True
        p.font.size = Pt(26)
        p.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

# Subtitle shape
for s in s1.shapes:
    if s != s1.shapes.title and s.has_text_frame and s.name != "TextBox 14":
        tf = s.text_frame
        tf.word_wrap = True
        tf.clear()
        
        lines = [
            ("Project Title: AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform", True, 17, RGBColor(0x0F, 0x17, 0x2A)),
            ("", False, 6, None),
            ("Batch Number: AIML C24", True, 14, RGBColor(0x1E, 0x40, 0xAF)),
            ("Guide Name: Mrs. UDHAYA J.M., M.E., Assistant Professor, Dept of AIML", True, 14, RGBColor(0x1E, 0x29, 0x3B)),
            ("", False, 6, None),
            ("Team Members:", True, 14, RGBColor(0x0F, 0x17, 0x2A)),
            ("  • SAJITH AR  (Reg No: 211423247183)", False, 13.5, RGBColor(0x33, 0x41, 0x55)),
            ("  • SARAN R   (Reg No: 211423247189)", False, 13.5, RGBColor(0x33, 0x41, 0x55)),
        ]
        for idx, (t, bold, sz, col) in enumerate(lines):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = t
            p.font.name = 'Arial'
            p.font.bold = bold
            p.font.size = Pt(sz)
            if col:
                p.font.color.rgb = col
update_footer_date(s1)

# ==========================================
# SLIDE 2: ABSTRACT
# ==========================================
s2 = prs.slides[1]
set_slide_title(s2, "Abstract")
content_shape = [s for s in s2.shapes if s.has_text_frame and s != s2.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
abstract_items = [
    ("Chennai Flood Lab: AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform", True, 14, RGBColor(0x1E, 0x3A, 0x8A)),
    ("", False, 6, None),
    ("During severe urban flooding events, rapid and equitable emergency resource distribution is vital to saving lives. Traditional disaster response relies on delayed field surveys, manual spreadsheet accounting, and static routing maps that ignore dynamic road submersions, leading to critical supply stockouts, vehicle stranding, and inequitable regional distribution.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
    ("", False, 5, None),
    ("This project presents an integrated, software-driven crisis management and logistics platform combining spatio-temporal inundation dynamics with machine learning and mathematical optimization. A 180-tree Gradient Boosted Decision Tree (GBDT) model trained on 9,131 daily NASA POWER reanalysis records predicts next-day elevated rainfall (>=10 mm/day, 87.12% ROC-AUC). Simultaneously, a 128-tree Extra Trees + Ridge regression blend predicts per-capita emergency drinking water, food rations, and medical kit demand, achieving up to 96.6% error reduction over heuristic rules.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
    ("", False, 5, None),
    ("Split-conformal calibration delivers finite-sample 90% confidence intervals for relief demand. NetworkX dynamically evaluates road network accessibility against water depths (0.5m evacuation, 0.3m truck limit), while Google OR-Tools solves capacity-constrained shelter allocation and multi-commodity depot logistics. A high-performance Next.js 14 / Leaflet dashboard enables sub-second (<0.45s) interactive scenario simulation, playback, and offline GCC ward atlas exploration.", False, 12, RGBColor(0x1E, 0x29, 0x3B))
]
for idx, (t, bold, sz, col) in enumerate(abstract_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
update_footer_date(s2)

# ==========================================
# SLIDE 3: MOTIVATION
# ==========================================
s3 = prs.slides[2]
set_slide_title(s3, "Motivation")
content_shape = [s for s in s3.shapes if s.has_text_frame and s != s3.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
motivation_items = [
    ("Why This Problem Matters", True, 14, RGBColor(0x1E, 0x3A, 0x8A)),
    ("• Increasing Severity of Urban Deluges: Rapid urbanization and climate change have intensified extreme rainfall events in coastal metros like Chennai (2015 floods, 2023 Cyclone Michaung), overwhelming municipal response systems.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
    ("• The 'Reactive' Supply Chain Flaw: Relief agencies historically dispatch supplies only after shortages are publicly reported, causing catastrophic delays in life-saving aid to severely inundated sectors.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Dynamic Infrastructure Volatility: Surface roads and arterial bridges submerge unevenly during active rainfall. Standard navigation tools lack real-time hydrological awareness, resulting in stranded rescue convoys.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Cognitive Overload & Inequitable Allocation: In severe scarcity, dispatchers face high cognitive strain balancing population density, medical urgency, and geographic vulnerability across 200 GCC wards without mathematical optimization.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Why Existing Approaches Fall Short: Standalone flood engines lack logistics coupling, while logistics algorithms assume fully accessible transit networks. An integrated, uncertainty-aware framework is urgently required.", False, 12, RGBColor(0x1E, 0x29, 0x3B)),
]
for idx, (t, bold, sz, col) in enumerate(motivation_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
    p.space_after = Pt(6)
update_footer_date(s3)

# ==========================================
# SLIDE 4: LITERATURE SURVEY 1
# ==========================================
s4 = prs.slides[3]
set_slide_title(s4, "Literature Survey")
clear_images_from_slide(s4)
s4.shapes.add_picture("generated_charts/lit_survey_1.png", Inches(0.6), Inches(1.3), Inches(12.1), Inches(4.9))
update_footer_date(s4)

# ==========================================
# SLIDE 5: LITERATURE SURVEY 2
# ==========================================
s5 = prs.slides[4]
set_slide_title(s5, "Literature Survey (Cont.)")
clear_images_from_slide(s5)
s5.shapes.add_picture("generated_charts/lit_survey_2.png", Inches(0.6), Inches(1.3), Inches(12.1), Inches(4.9))
update_footer_date(s5)

# ==========================================
# SLIDE 6: DISADVANTAGES OF EXISTING SYSTEM
# ==========================================
s6 = prs.slides[5]
set_slide_title(s6, "Disadvantages of Existing System")
content_shape = [s for s in s6.shapes if s.has_text_frame and s != s6.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
disadv_items = [
    ("• Manual Data Processing Bottlenecks", True, 13, RGBColor(0x99, 0x1B, 0x1B)),
    ("  Relying on human dispatchers to manually log damage reports and update spreadsheets causes critical multi-hour lags during fast-moving flood surges.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ("• Purely Reactive Inventory Tracking", True, 13, RGBColor(0x99, 0x1B, 0x1B)),
    ("  Existing emergency platforms track static depot inventory and only alert coordinators after shortages occur, precluding proactive supply pre-positioning.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ("• Suboptimal & Biased Resource Allocation", True, 13, RGBColor(0x99, 0x1B, 0x1B)),
    ("  When critical supplies are scarce, manual distribution fails to mathematically optimize priority coverage across shelters, resulting in severe regional inequities.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ("• Static GIS Mapping & Ignored Road Submersion", True, 13, RGBColor(0x99, 0x1B, 0x1B)),
    ("  Standard navigation tools assume roads are passable until user accidents occur, leading delivery trucks into submerged arterial bottlenecks (>=0.30m depth).", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ("• Isolated Monolithic Systems & Lack of Uncertainty Bounds", True, 13, RGBColor(0x99, 0x1B, 0x1B)),
    ("  Point-prediction ML tools fail to provide confidence intervals, leaving emergency planners without statistical safety buffers for worst-case surges.", False, 11.5, RGBColor(0x33, 0x41, 0x55))
]
for idx, (t, bold, sz, col) in enumerate(disadv_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
    p.space_after = Pt(2 if bold else 5)
update_footer_date(s6)

# ==========================================
# SLIDE 7: PROPOSED SYSTEM
# ==========================================
s7 = prs.slides[6]
set_slide_title(s7, "Proposed System")
content_shape = [s for s in s7.shapes if s.has_text_frame and s != s7.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
proposed_items = [
    ("AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform", True, 13.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("• Spatio-Temporal Inundation Dynamics", True, 12, RGBColor(0x0F, 0x76, 0x6E)),
    ("  Simulates continuous flood spread and water depth decay across discrete time steps (t=0..T) with depth thresholds (0.50m evacuation, 0.30m logistics).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Dual Predictive AI Engine", True, 12, RGBColor(0x0F, 0x76, 0x6E)),
    ("  A 180-tree GBDT model predicts next-day heavy rainfall from NASA POWER reanalysis (87.12% AUC), and a 128-tree Extra Trees/Ridge ensemble predicts per-person relief demands.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Split-Conformal Uncertainty Calibration", True, 12, RGBColor(0x0F, 0x76, 0x6E)),
    ("  Distribution-free finite-sample conformal calibration generates verified 90% confidence intervals for water, food, and medical kit demand.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Mathematical Linear Programming Allocation", True, 12, RGBColor(0x0F, 0x76, 0x6E)),
    ("  Google OR-Tools GLOP optimizer guarantees equitable, capacity-constrained shelter assignments and depot stock conservation with transaction rollback.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Dynamic Flood-Avoidance Routing & Dedicated Fleet Dispatch", True, 12, RGBColor(0x0F, 0x76, 0x6E)),
    ("  NetworkX dynamically updates Chennai OSM road graph weights, calculating safe A*/Dijkstra paths and coordinating dedicated truck, boat, and airlift fleets.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Full-Stack Next.js 14 Interactive Dashboard", True, 12, RGBColor(0x0F, 0x76, 0x6E)),
    ("  Enables real-time scenario simulation (<0.45s), timeline playback, bilingual Tamil/English bulletins, 200-ward GCC atlas, and HTML report export.", False, 11, RGBColor(0x33, 0x41, 0x55))
]
for idx, (t, bold, sz, col) in enumerate(proposed_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
    p.space_after = Pt(1 if bold else 4)
update_footer_date(s7)

# ==========================================
# SLIDE 8: GOAL
# ==========================================
s8 = prs.slides[7]
set_slide_title(s8, "Goal & Key Objectives")
content_shape = [s for s in s8.shapes if s.has_text_frame and s != s8.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
goal_items = [
    ("Primary Goal", True, 13.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("To build a working prototype that detects flood risk from meteorological reanalysis, forecasts multi-commodity relief demand with conformal uncertainty bounds, dynamically routes logistics around inundated roads, and optimizes shelter assignments—demonstrated live on a full-stack GIS dashboard.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("", False, 4, None),
    ("Specific Technical Objectives:", True, 13, RGBColor(0x0F, 0x17, 0x2A)),
    ("• Train 180-Tree GBDT weather model on 9,131 days of NASA POWER data (Target: >=85% ROC-AUC).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Build 128-Tree Extra Trees + Ridge ensemble reducing relief demand MAE by >=85% over rule baselines.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Implement split-conformal calibration guaranteeing nominal 90% coverage on held-out disaster events.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Dynamically screen Chennai OSM road graph in NetworkX (evacuation cutoff 0.50m, truck cutoff 0.30m).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Deploy Google OR-Tools GLOP solver for equitable resource allocation and strict inventory conservation.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Build full-stack Next.js 14 / FastAPI platform executing complete scenarios in <0.45 seconds.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("", False, 4, None),
    ("Success Metric: Examiner can interact live with the dashboard—draw flood polygons or select presets—and view verified routing, shelter allocation, and demand intervals within 1 second.", True, 11.5, RGBColor(0x04, 0x78, 0x57))
]
for idx, (t, bold, sz, col) in enumerate(goal_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
    p.space_after = Pt(2)
update_footer_date(s8)

# ==========================================
# SLIDE 9: ARCHITECTURAL DIAGRAM
# ==========================================
s9 = prs.slides[8]
set_slide_title(s9, "Architectural Diagram")
content_shape = [s for s in s9.shapes if s.has_text_frame and s != s9.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
arch_items = [
    ("System Overview — 7-Layer Resilient Pipeline", True, 13.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("• Layer 1 — Input & Scenario Setup: Interactive flood polygon drawing, circular radius (500-5000m), historical disaster presets (Velachery, Adyar, Mudichur, T. Nagar).", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Layer 2 — Spatial Data Ingestion: Bundled OSM Chennai arterial road graph, 200 GCC Wards, 12 Shelters, 5 Warehouses, 10 Distribution Hubs.", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Layer 3 — Inundation Dynamics Engine: Spatio-temporal flood progression and depth decay model across time steps t=0..T.", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Layer 4 — Dynamic Road Graph Screening: Depth-based edge impedance and impassable corridor removal in NetworkX (0.5m evacuation, 0.3m trucks).", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Layer 5 — Dual Predictive ML Engine: NASA POWER 180-tree rainfall classifier + 128-tree Extra Trees/Ridge demand forecaster.", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Layer 6 — Conformal Calibration & Optimization: Nominal 90% confidence intervals + Google OR-Tools capacity-constrained linear programming solver.", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Layer 7 — Multi-Modal Routing & GIS Visualization: Safe evacuation paths, dedicated rescue fleet dispatch (trucks, boats, helicopters), Next.js dashboard.", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("", False, 4, None),
    ("Key Design Insight: Combining predictive weather classification with dynamic graph impedance and mathematical resource optimization provides guaranteed stock conservation and flood-free transit.", True, 11.5, RGBColor(0x04, 0x78, 0x57))
]
for idx, (t, bold, sz, col) in enumerate(arch_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
    p.space_after = Pt(2)
update_footer_date(s9)

# ==========================================
# SLIDE 10: ARCHITECTURAL FLOWCHART (IMAGE)
# ==========================================
s10 = prs.slides[9]
clear_images_from_slide(s10)
# Add architecture flowchart centered
s10.shapes.add_picture("generated_charts/architecture_flow.png", Inches(3.2), Inches(0.4), Inches(6.8), Inches(6.0))
update_footer_date(s10)

# ==========================================
# SLIDE 11: MODULES EXPLANATION
# ==========================================
s11 = prs.slides[10]
set_slide_title(s11, "Modules — Explanation of Architectural Diagram")
content_shape = [s for s in s11.shapes if s.has_text_frame and s != s11.shapes.title and "Footer" not in s.name and "TextBox" not in s.name][0]
tf = content_shape.text_frame
tf.word_wrap = True
tf.clear()
module_items = [
    ("Module 1 — Data & Scenario Ingestion", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("Validates scenario parameters (intensity 1-5, depth 0.1-3.0m, spread rate) and spatial inputs across 200 GCC wards and OSM road networks.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("Module 2 — Inundation Dynamics & Graph Pruning", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("Calculates temporal flood buffers and water depth decay. Dynamically prunes NetworkX road graph edges exceeding safe transit depths (0.50m evacuation, 0.30m trucks).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("Module 3 — Dual Predictive ML Engine", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("NASA POWER 180-tree GBDT model classifies next-day rainfall hazard (>=10mm, 87.12% AUC). 128-Tree Extra Trees + Ridge ensemble predicts per-capita water, food, and medical demand.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("Module 4 — Split-Conformal Calibration", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("Computes finite-sample non-conformity scores on dedicated calibration data, producing distribution-free 90% prediction intervals with humanitarian minimum safety floors.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("Module 5 — Mathematical Optimization (OR-Tools)", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("Formulates multi-commodity distribution as a Linear Program (GLOP), enforcing shelter capacities, depot stock bounds, and transaction rollback.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("Module 6 — Dynamic Routing & Multi-Modal Fleet", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("Solves shortest-path Dijkstra/A* routing for evacuation and dispatches configured rescue trucks, flood-rescue boats, and airlift units to isolated ward clusters.", False, 11, RGBColor(0x33, 0x41, 0x55))
]
for idx, (t, bold, sz, col) in enumerate(module_items):
    p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
    p.text = t
    p.font.name = 'Arial'
    p.font.bold = bold
    p.font.size = Pt(sz)
    if col:
        p.font.color.rgb = col
    p.space_after = Pt(1 if bold else 3)
update_footer_date(s11)

# Helper function to configure a 2-column slide with bullets on left, image on right
def configure_two_column_slide(slide, title, bullets, image_path, img_w=5.5, img_h=4.2, img_top=1.8, img_left=7.2):
    set_slide_title(slide, title)
    clear_images_from_slide(slide)
    
    # Left text shape
    text_shapes = [s for s in slide.shapes if s.has_text_frame and s != slide.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
    if text_shapes:
        left_shape = text_shapes[0]
        left_shape.left = Inches(0.6)
        left_shape.top = Inches(1.8)
        left_shape.width = Inches(6.3)
        left_shape.height = Inches(4.5)
        tf = left_shape.text_frame
        tf.word_wrap = True
        tf.clear()
        for idx, (b_text, is_bold, sz, col) in enumerate(bullets):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.text = b_text
            p.font.name = 'Arial'
            p.font.bold = is_bold
            p.font.size = Pt(sz)
            if col:
                p.font.color.rgb = col
            p.space_after = Pt(4)
            
    # Right image
    if image_path and os.path.exists(image_path):
        slide.shapes.add_picture(image_path, Inches(img_left), Inches(img_top), Inches(img_w), Inches(img_h))
    update_footer_date(slide)

# ==========================================
# SLIDE 12: DATASET STATISTICS
# ==========================================
s12 = prs.slides[11]
s12_bullets = [
    ("• NASA POWER Chennai Weather Dataset:", True, 12.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  9,131 daily records (2001-2025) at latitude 13.0827, longitude 80.2707.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ("• Meteorological Attributes (13 Features):", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Precipitation, temp, humidity, wind, pressure, 3/7-day lags, and cyclic seasonality.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Strict Chronological Split Protocol:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Training: 6,567 days (2001-2018) | Val: 1,096 days (2019-2021) | Test: 1,461 days (2022-2025).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Multi-Scenario Relief Demand Dataset:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  55,000 synthetic disaster rows; complete hold-out of 2023 Cyclone Michaung (16,513 rows).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Spatial Infrastructure Inventory:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  12 verified public shelters (5,400 capacity), 5 depots, 10 distribution hubs, 200 wards.", False, 11, RGBColor(0x33, 0x41, 0x55)),
]
configure_two_column_slide(s12, "DATASET STATISTICS", s12_bullets, "generated_charts/dataset_statistics_table.png", img_w=5.6, img_h=4.5, img_top=1.7, img_left=7.1)

# ==========================================
# SLIDE 13: MODEL EVALUATION
# ==========================================
s13 = prs.slides[12]
s13_bullets = [
    ("• Multi-Model Comparative Framework:", True, 12.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Evaluated Gradient Boosted Trees (180 depth-2 trees, lr=0.04), Random Forest (300 estimators), and Persistence baselines for weather.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Multi-Output Relief Demand Ensemble:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  64 Extra Trees, 64 Random Forest, and Scaled Ridge Regression with convex out-of-event weight grid optimization.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Strict Held-Out Evaluation:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Zero-leakage testing on chronological 2022-2025 weather reanalysis and Cyclone Michaung disaster group.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Superior Life-Safety Metrics:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Selected Gradient Boosted model achieved 0.8712 ROC-AUC and 80.36% Recall, prioritizing emergency warning responsiveness.", False, 11, RGBColor(0x04, 0x78, 0x57)),
]
configure_two_column_slide(s13, "MODEL EVALUATION", s13_bullets, "generated_charts/model_performance_comparison.png", img_w=5.7, img_h=4.4, img_top=1.8, img_left=7.0)

# ==========================================
# SLIDE 14: CONFIDENCE CALIBRATION & UNCERTAINTY
# ==========================================
s14 = prs.slides[13]
s14_bullets = [
    ("• Split-Conformal Prediction Framework:", True, 12.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Employs distribution-free inductive conformal prediction on 9,622 independent calibration rows.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Finite-Sample Mathematical Coverage:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Achieves nominal 90% marginal coverage on held-out test data (Water: 89.81%, Food: 90.29%, Medical Kits: 93.90%).", False, 11, RGBColor(0x04, 0x78, 0x57)),
    ("• Reliable Emergency Safety Margins:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Automatically bounds demand upper and lower estimates to prevent supply deficits under extreme surges.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Humanitarian Planning Minimums:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Enforces strict safety floors (3.0 L drinking water, 3.0 food units, 0.02 medical kits per capita) to prevent degenerate allocations.", False, 11, RGBColor(0x33, 0x41, 0x55)),
]
configure_two_column_slide(s14, "CONFIDENCE CALIBRATION AND EXPLAINABILITY", s14_bullets, "generated_charts/confidence_calibration.png", img_w=5.7, img_h=4.4, img_top=1.8, img_left=7.0)

# ==========================================
# SLIDE 15: WHY CHOSEN MODELS?
# ==========================================
s15 = prs.slides[14]
set_slide_title(s15, "WHY GRADIENT BOOSTING & EXTRA TREES?")
clear_images_from_slide(s15)
text_shapes = [s for s in s15.shapes if s.has_text_frame and s != s15.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
if text_shapes:
    tf = text_shapes[0].text_frame
    tf.word_wrap = True
    tf.clear()
    why_items = [
        ("• Tabular Data Superiority:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Meteorological variables and disaster relief factors are structured tabular matrices where shallow tree ensembles consistently outperform deep networks without overfitting.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Pure-Python Zero-Dependency Inference:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Deployed models are exported as lightweight JSON decision trees and linear coefficients, executing in <1.2 ms with standard Python dictionaries—no PyTorch or GPU required.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Asymmetric Recall Optimization:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Shallow depth-2 gradient boosting with validation-tuned decision thresholds achieves 80.36% recall, critically minimizing missed disaster warnings.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Robust Out-of-Event Generalization:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Blending Extra Trees with Ridge regression dampens variance across extreme out-of-event disaster scenarios.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Provenance & Auditability:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  SHA-256 fingerprinting for datasets and model weights guarantees exact auditability and zero drift during panel evaluation.", False, 11.5, RGBColor(0x33, 0x41, 0x55))
    ]
    for idx, (t, bold, sz, col) in enumerate(why_items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = t
        p.font.name = 'Arial'
        p.font.bold = bold
        p.font.size = Pt(sz)
        if col:
            p.font.color.rgb = col
        p.space_after = Pt(2 if bold else 6)
update_footer_date(s15)

# ==========================================
# SLIDE 16: SYSTEM ARCHITECTURE OVERVIEW
# ==========================================
s16 = prs.slides[15]
s16_bullets = [
    ("• Input Layer:", True, 12.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  13 NASA atmospheric features + Chennai 200 GCC wards and OSM road network.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Inundation Dynamics Engine:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Geometric flood spread with depth-dependent road screening (0.50m evacuation, 0.30m logistics).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Dual Machine Learning Inference:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  180-Tree GBDT weather classifier + 128-Tree Extra Trees/Ridge demand ensemble.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Conformal Uncertainty Calibration:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Split-conformal 90% confidence intervals with planning floors.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Mathematical Optimization:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Google OR-Tools GLOP solver for capacity-constrained allocation.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Output & Operational Visualization:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  Flood-avoidant evacuation routes, fleet dispatch plans, and interactive GIS visualization.", False, 11, RGBColor(0x04, 0x78, 0x57)),
]
configure_two_column_slide(s16, "System Architecture Overview", s16_bullets, "generated_charts/system_pipeline.png", img_w=5.6, img_h=4.5, img_top=1.7, img_left=7.1)

# ==========================================
# SLIDE 17: ARCHITECTURE FLOW / PIPELINE
# ==========================================
s17 = prs.slides[16]
set_slide_title(s17, "Architecture Flow & Pipeline Execution")
clear_images_from_slide(s17)
text_shapes = [s for s in s17.shapes if s.has_text_frame and s != s17.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
if text_shapes:
    tf = text_shapes[0].text_frame
    tf.word_wrap = True
    tf.clear()
    flow_steps = [
        "1. Dataset Ingestion: NASA POWER 9,131 daily records, GCC 200 wards, OSM Chennai road network.",
        "2. Hydrological Simulation: Dynamic flood polygon dilation and depth decay across time steps t=0..T.",
        "3. Road Graph Pruning: NetworkX screens road segments; closes routes with depth >= 0.50m (evacuation) or >= 0.30m (trucks).",
        "4. Shelter Accessibility Screening: Identifies safe, non-inundated public shelters from 12 verified municipal locations.",
        "5. Machine Learning Demand Prediction: 128-Tree Extra Trees + Ridge ensemble infers per-person resource needs.",
        "6. Split-Conformal Interval Calculation: Generates verified 90% upper and lower demand confidence bounds.",
        "7. Mathematical Resource Allocation: Google OR-Tools GLOP solver optimizes relief dispatch under inventory conservation.",
        "8. Dynamic Evacuation & Multi-Modal Routing: A* shortest path finds safe corridors; identifies stranded populations for boat/airlift dispatch.",
        "9. Interactive Dashboard & Report Generation: Next.js GIS UI visualizes results in <0.45s and exports self-contained HTML reports."
    ]
    for idx, step_text in enumerate(flow_steps):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = step_text
        p.font.name = 'Arial'
        p.font.size = Pt(11.5)
        p.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
        p.space_after = Pt(4)
update_footer_date(s17)

# ==========================================
# SLIDE 18: BASELINE COMPARISON
# ==========================================
s18 = prs.slides[17]
s18_bullets = [
    ("• Relief Demand Prediction Comparison:", True, 12.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  - Drinking Water: Rule MAE 3,647.53 L vs Proposed ML 122.44 L (96.6% Error Reduction).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("  - Food Rations: Rule MAE 1,843.65 vs Proposed ML 92.69 units (95.0% Error Reduction).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("  - Medical Kits: Rule MAE 91.54 vs Proposed ML 10.90 kits (88.1% Error Reduction).", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Weather Classification Comparison:", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("  - Proposed GBDT: 0.8712 ROC-AUC | 78.62% Balanced Acc | 80.36% Recall.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("  - Previous-Day Persistence: 0.7138 ROC-AUC | 71.38% Balanced Acc | 49.40% Recall.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("  - Always Low Baseline: 0.5000 ROC-AUC | 50.00% Balanced Acc | 0.00% Recall.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Key Observation:", True, 12, RGBColor(0x04, 0x78, 0x57)),
    ("  Proposed ML achieves dramatic error reduction across all metrics while prioritizing life safety.", False, 11, RGBColor(0x04, 0x78, 0x57)),
]
configure_two_column_slide(s18, "Baseline Comparison", s18_bullets, "generated_charts/baseline_comparison.png", img_w=5.7, img_h=4.4, img_top=1.8, img_left=7.0)

# ==========================================
# SLIDE 19: TRAINING DYNAMICS
# ==========================================
s19 = prs.slides[18]
s19_bullets = [
    ("• 5-fold cross-validation evaluated model stability across chronological and event-based data splits.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Gradient Boosted weather model achieved consistent ROC-AUC across all folds.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Fold-wise ROC-AUC: 0.862, 0.884, 0.871, 0.855, 0.884.", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("• Mean ROC-AUC: 0.871 ± 0.012.", True, 12, RGBColor(0x04, 0x78, 0x57)),
    ("• No fold scored below 0.85, confirming reliable predictive performance across diverse monsoon seasons.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• GroupKFold on relief demand models verified generalization across distinct historical flood profiles without data leakage.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
]
configure_two_column_slide(s19, "Training Dynamics — 5-Fold Cross-Validation", s19_bullets, "generated_charts/cross_validation_roc.png", img_w=5.7, img_h=4.4, img_top=1.8, img_left=7.0)

# ==========================================
# SLIDE 20: PREDICTION ACCURACY
# ==========================================
s20 = prs.slides[19]
s20_bullets = [
    ("• Proposed GBDT weather model achieved 87.12% ROC-AUC on held-out test data (2022-2025).", True, 12, RGBColor(0x1E, 0x3A, 0x8A)),
    ("• Balanced Accuracy: 78.62%.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Sensitivity / Recall: 80.36% (Correctly detected 135 of 168 elevated rainfall days).", True, 12, RGBColor(0x04, 0x78, 0x57)),
    ("• Raw Test Accuracy: 77.28%.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Precision: 31.11% (Reflects conservative, safety-first thresholding).", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• F1-Score: 44.85% (Substantial improvement over zero baseline).", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
    ("• The model demonstrates strong discriminative capability for early flood warning with minimal missed alarms.", False, 11.5, RGBColor(0x1E, 0x29, 0x3B)),
]
configure_two_column_slide(s20, "Prediction Accuracy", s20_bullets, "generated_charts/prediction_accuracy.png", img_w=5.7, img_h=4.4, img_top=1.8, img_left=7.0)

# ==========================================
# SLIDE 21: GRAPH INSIGHTS & CONFUSION MATRIX
# ==========================================
s21 = prs.slides[20]
s21_bullets = [
    ("• Figure 1: Test-Set performance comparison confirms GBDT dominates persistence in Recall (80.4% vs 49.4%) and ROC-AUC (0.871 vs 0.714).", False, 11, RGBColor(0x1E, 0x29, 0x3B)),
    ("• Figure 2: Confusion matrix shows 994 true negatives, 135 true positives, and only 33 false negatives over 4 test years.", True, 11.5, RGBColor(0x1E, 0x3A, 0x8A)),
    ("• The 80.4% recall ensures timely disaster mobilization with minimal missed hazardous events.", False, 11, RGBColor(0x04, 0x78, 0x57)),
    ("• Feature importance analysis reveals 7-day cumulative precipitation and relative humidity as primary drivers.", False, 11, RGBColor(0x33, 0x41, 0x55)),
    ("• Conformal interval widths remain stable across diverse scenario severities.", False, 11, RGBColor(0x33, 0x41, 0x55)),
]
configure_two_column_slide(s21, "Graph Insights & Confusion Matrix Analysis", s21_bullets, "generated_charts/confusion_matrix.png", img_w=5.2, img_h=4.5, img_top=1.7, img_left=7.2)

# ==========================================
# SLIDE 22: DISCUSSION
# ==========================================
s22 = prs.slides[21]
set_slide_title(s22, "Discussion")
clear_images_from_slide(s22)
text_shapes = [s for s in s22.shapes if s.has_text_frame and s != s22.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
if text_shapes:
    tf = text_shapes[0].text_frame
    tf.word_wrap = True
    tf.clear()
    disc_items = [
        ("• Integrated Cross-Domain Architecture:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Bridges atmospheric reanalysis, spatio-temporal inundation dynamics, operations research, and graph algorithms into a unified platform.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Life-Safety First Optimization:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Calibrating models for high recall (80.4%) and providing conformal 90% upper bounds prevents shelter supply shortages during extreme rainfall surges.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Provable Stock Conservation:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Google OR-Tools GLOP solver ensures allocations never exceed depot inventory; atomic transaction rollback prevents corrupted ledger states on network disruptions.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Sub-Second Real-Time Responsiveness:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Pure-Python graph algorithms and lightweight JSON tree traversal compute complete multi-step simulations in <0.45s, facilitating live interactive examiner demonstrations.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Transparent Scientific Boundaries:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Explicitly acknowledges synthetic demand labels and simplified road geometry while establishing a reproducible foundation for future hydraulic coupling.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ]
    for idx, (t, bold, sz, col) in enumerate(disc_items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = t
        p.font.name = 'Arial'
        p.font.bold = bold
        p.font.size = Pt(sz)
        if col:
            p.font.color.rgb = col
        p.space_after = Pt(2 if bold else 5)
update_footer_date(s22)

# ==========================================
# SLIDE 23: CONCLUSION
# ==========================================
s23 = prs.slides[22]
set_slide_title(s23, "Conclusion")
clear_images_from_slide(s23)
text_shapes = [s for s in s23.shapes if s.has_text_frame and s != s23.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
if text_shapes:
    tf = text_shapes[0].text_frame
    tf.word_wrap = True
    tf.clear()
    conc_items = [
        ("• High-Performance Hazard Prediction:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Developed and verified a 180-tree GBDT model achieving 87.12% ROC-AUC and 80.36% recall on 4 years of untouched NASA weather reanalysis.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Significant Relief Error Reduction:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Extra Trees + Ridge ensemble reduces demand prediction MAE by 88.1% to 96.6% compared to traditional planning rules, backed by nominal 90% conformal intervals.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Dynamic Flood-Avoidant Routing:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Implemented dynamic NetworkX graph routing that automatically isolates submerged corridors (>=0.30m trucks, >=0.50m pedestrians) and coordinates multi-modal rescue fleets.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Mathematically Optimal Allocation:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Google OR-Tools GLOP solver guarantees equitable, capacity-compliant shelter and supply distribution with strict stock conservation.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Full-Stack Operational Platform:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Built an interactive Next.js 14 / FastAPI application featuring a 200-ward GCC atlas, bilingual Tamil/English bulletins, timeline playback, and reproducible exports.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ]
    for idx, (t, bold, sz, col) in enumerate(conc_items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = t
        p.font.name = 'Arial'
        p.font.bold = bold
        p.font.size = Pt(sz)
        if col:
            p.font.color.rgb = col
        p.space_after = Pt(2 if bold else 5)
update_footer_date(s23)

# ==========================================
# SLIDE 24: FUTURE WORK
# ==========================================
s24 = prs.slides[23]
set_slide_title(s24, "Future Work")
clear_images_from_slide(s24)
text_shapes = [s for s in s24.shapes if s.has_text_frame and s != s24.shapes.title and "Footer" not in s.name and "TextBox" not in s.name]
if text_shapes:
    tf = text_shapes[0].text_frame
    tf.word_wrap = True
    tf.clear()
    fw_items = [
        ("• Hydrodynamic PDE Integration:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Couple 2D shallow water equation solvers (LISFLOOD-FP / SWMM) with high-resolution LiDAR Digital Elevation Models for physics-based flood routing.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Real-Time IoT Telemetry:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Integrate live ultrasonic water-level sensors and automatic rain gauges across Adyar and Cooum river basins for continuous automated data feeds.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Vehicle Routing with Time Windows (VRPTW):", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Expand OR-Tools logistics to solve multi-vehicle routing with fleet battery/fuel limits, driver shift constraints, and dynamic pickup requests.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Offline Mobile Edge Deployment:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Package the lightweight JSON inference runtime into Progressive Web Apps (PWA) and Android offline APKs for frontline disaster responders.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
        ("• Empirical Field Validation:", True, 13, RGBColor(0x1E, 0x3A, 0x8A)),
        ("  Partner with Tamil Nadu Disaster Management Authority (TNDMA) for real-world validation against observed flood logistics records.", False, 11.5, RGBColor(0x33, 0x41, 0x55)),
    ]
    for idx, (t, bold, sz, col) in enumerate(fw_items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = t
        p.font.name = 'Arial'
        p.font.bold = bold
        p.font.size = Pt(sz)
        if col:
            p.font.color.rgb = col
        p.space_after = Pt(2 if bold else 5)
update_footer_date(s24)

# ==========================================
# SLIDE 25: THANK YOU
# ==========================================
s25 = prs.slides[24]
if s25.shapes.title:
    s25.shapes.title.text = "Thank You !!!"
    for p in s25.shapes.title.text_frame.paragraphs:
        p.font.name = 'Arial'
        p.font.bold = True
        p.font.size = Pt(36)
        p.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

# ==========================================
# SLIDE 26: QUERIES?
# ==========================================
s26 = prs.slides[25]
if s26.shapes.title:
    s26.shapes.title.text = "Queries?"
    for p in s26.shapes.title.text_frame.paragraphs:
        p.font.name = 'Arial'
        p.font.bold = True
        p.font.size = Pt(36)
        p.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

# Save presentation
primary_out_path = os.path.join(OUTPUT_DIR, PRIMARY_FILENAME)
prs.save(primary_out_path)
print(f"Saved primary presentation to: {primary_out_path}")

# Also save alternative filenames for team number matching
alt_names = [
    "AIML C24 - AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform.pptx"

]
for alt in alt_names:
    alt_path = os.path.join(OUTPUT_DIR, alt)
    prs.save(alt_path)
    print(f"Saved alternative presentation to: {alt_path}")

print("All presentations built successfully!")
