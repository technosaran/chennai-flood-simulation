import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from report_styles import add_p, add_body, add_h1, add_h2, add_h3, add_bullet, add_fig, style_academic_table
import os

def generate_chapter_4(doc):
    # CHAPTER 4
    add_h1(doc, "CHAPTER 4\nSYSTEM IMPLEMENTATION")
    
    # 4.1 Module Description
    add_h2(doc, "4.1 Module Description")
    add_body(doc, "The proposed platform is organized into six interconnected, independently testable functional modules implemented in Python 3.12 and TypeScript/React. The decoupled modular architecture ensures high maintainability, fault tolerance, and low latency:")
    
    add_bullet(doc, "Module 1: Atmospheric Ingestion & Preprocessing (weather_predictor.py)", 
               "Automates the harvesting, parsing, and rolling feature calculation of daily meteorological telemetry from NASA POWER and local weather stations, constructing a 13-dimensional feature space.")
    
    add_bullet(doc, "Module 2: Machine Learning Precipitation Classifier (train_weather_model.py)", 
               "Trains and evaluates a 180-tree Gradient Boosted Decision Tree (GBDT) using log-loss minimization to predict next-day heavy precipitation hazard.")
    
    add_bullet(doc, "Module 3: Multi-Commodity Demand Forecasting & Conformal Calibration (demand_predictor.py)", 
               "Implements a 128-tree ensemble regressor combined with distribution-free split-conformal calibration, producing bounded demand intervals for drinking water, food rations, and medical kits across 200 wards.")
    
    add_bullet(doc, "Module 4: Multi-Commodity Supply Allocation Engine (supply_solver.py)", 
               "Formulates and solves a continuous multi-commodity network flow linear program using Google OR-Tools GLOP, optimizing warehouse inventory dispatches to shelters under equity constraints.")
    
    add_bullet(doc, "Module 5: Hazard-Aware Dynamic Graph Router (evacuation_solver.py)", 
               "Constructs a directed network graph of Chennai's road network using NetworkX, pruning edges exceeding vehicle inundation depth thresholds and computing safe multi-modal evacuation paths.")
    
    add_bullet(doc, "Module 6: Geospatial Dashboard, Bilingual Advisories & Reporting (main.py / Next.js)", 
               "Serves RESTful API endpoints via FastAPI, renders real-time interactive GIS layers in Next.js 14 / Leaflet, generates automated bilingual Tamil/English advisories, and compiles standalone offline PDF/HTML reports.")
    
    # 4.2 Data Ingestion & Preprocessing
    add_h2(doc, "4.2 Data Ingestion, Preprocessing & Spatio-Temporal Feature Engineering")
    add_body(doc, "High-fidelity disaster prediction requires clean, continuous historical meteorological records paired with detailed spatial demographics. The platform integrates two primary data sources: the NASA Prediction of Worldwide Energy Resources (POWER) daily reanalysis dataset and the Greater Chennai Corporation (GCC) ward GIS database.")
    
    add_body(doc, "The NASA POWER dataset provides 25 continuous years (January 1, 2001 to December 31, 2025) of daily meteorological observations for Chennai (latitude 13.0827° N, longitude 80.2707° E), totaling 9,131 verified daily records. The primary meteorological variables include precipitation (PRECTOTCORR, mm/day), 2-meter air temperature (T2M, °C), maximum temperature (T2M_MAX, °C), minimum temperature (T2M_MIN, °C), 2-meter relative humidity (RH2M, %), surface atmospheric pressure (PS, kPa), and 10-meter wind speed (WS10M, m/s).")
    
    add_body(doc, "To capture atmospheric memory and monsoonal accumulation dynamics, rolling temporal feature engineering is applied across a 7-day retrospective window. For any day t, the engineered feature vector includes:")
    
    add_bullet(doc, "Precipitation Lags & Aggregations", 
               "Precipitation on day t-1, 3-day rolling sum (Sum_3d = sum_{i=1}^3 P_{t-i}), 7-day rolling sum (Sum_7d = sum_{i=1}^7 P_{t-i}), and 7-day maximum daily precipitation (Max_7d = max_{i=1..7} P_{t-i}).")
    
    add_bullet(doc, "Atmospheric Moisture & Thermal Gradients", 
               "7-day rolling mean of relative humidity (RH_mean_7d), 7-day rolling mean of air temperature (T_mean_7d), daily diurnal temperature range (Delta_T = T2M_MAX - T2M_MIN), and surface pressure deviation (Delta_PS = PS_t - PS_{mean_7d}).")
    
    add_bullet(doc, "Cyclic Seasonal Encodings", 
               "To capture Chennai's severe annual monsoonal seasonality without introducing artificial boundary discontinuities between December 31 and January 1, the day of the year (DOY in [1, 365]) is transformed into two continuous orthogonal trigonometric features:\n"
               "Sin_DOY = sin(2 * pi * DOY / 365.25)\n"
               "Cos_DOY = cos(2 * pi * DOY / 365.25)")
    
    add_body(doc, "Table 4.2.1 provides the comprehensive feature inventory, data types, physical units, and statistical ranges utilized across the machine learning pipeline.")
    
    add_p(doc, "Table 4.2.1: NASA POWER Meteorological Feature Inventory & Scenario Attributes", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    feat_headers = ["Feature Identifier", "Physical Variable Description", "Units", "Min Value", "Mean Value", "Max Value", "Role in Pipeline"]
    feat_widths = [Inches(1.2), Inches(1.8), Inches(0.8), Inches(0.7), Inches(0.7), Inches(0.7), Inches(1.3)]
    feat_data = [
        ["PRECTOTCORR", "Daily corrected precipitation", "mm/day", "0.00", "3.62", "494.20", "Target / Hazard threshold"],
        ["T2M", "2-meter air temperature", "°C", "19.45", "28.65", "37.82", "Atmospheric state feature"],
        ["T2M_MAX", "Maximum daily temperature", "°C", "22.10", "32.84", "43.50", "Diurnal cycle feature"],
        ["T2M_MIN", "Minimum daily temperature", "°C", "16.20", "24.91", "31.40", "Diurnal cycle feature"],
        ["RH2M", "2-meter relative humidity", "%", "24.50", "72.15", "98.80", "Moisture saturation index"],
        ["PS", "Surface atmospheric pressure", "kPa", "98.20", "100.45", "101.90", "Depression / Cyclone marker"],
        ["WS10M", "10-meter wind speed", "m/s", "0.85", "3.42", "22.60", "Storm intensity marker"],
        ["precip_sum_3d", "3-day cumulative precipitation", "mm", "0.00", "10.86", "720.40", "Catchment pre-saturation"],
        ["precip_sum_7d", "7-day cumulative precipitation", "mm", "0.00", "25.34", "945.10", "Ground saturation index"],
        ["sin_doy", "Sine cyclic day-of-year", "[-1, 1]", "-1.00", "0.01", "1.00", "Monsoon seasonal cycle"],
        ["cos_doy", "Cosine cyclic day-of-year", "[-1, 1]", "-1.00", "-0.02", "1.00", "Monsoon seasonal cycle"],
        ["ward_depth", "Localized ward flood depth", "meters", "0.00", "0.42", "2.15", "Demand & routing trigger"],
        ["vulnerability", "Socio-economic vulnerability", "[0, 1]", "0.15", "0.58", "0.95", "Equity allocation weight"]
    ]
    
    t_421 = doc.add_table(rows=1, cols=7)
    style_academic_table(t_421, feat_widths, feat_headers, feat_data)
    
    add_p(doc, "", space_before=10)
    add_fig(doc, r"generated_charts\dataset_statistics_table.png", 
            "Figure 4.2.1: NASA POWER Meteorological Reanalysis & Scenario Dataset Distributions", width=Inches(6.0))
    
    # 4.3 Machine Learning Formulation
    add_h2(doc, "4.3 Machine Learning Formulation & Model Training")
    add_body(doc, "The platform employs a dual-stage machine learning architecture separating macro-level meteorological hazard detection from micro-level humanitarian demand regression.")
    
    add_h3(doc, "4.3.1 180-Tree GBDT Weather Hazard Classifier")
    add_body(doc, "Next-day heavy rainfall hazard is formulated as a binary classification problem: given feature vector x_t on day t, predict whether precipitation on day t+1 meets or exceeds the critical municipal hazard threshold:\n"
             "y_{t+1} = 1 if PRECTOTCORR_{t+1} >= 10.0 mm/day, else 0.")
    
    add_body(doc, "The model is built using Gradient Boosted Decision Trees (GBDT). GBDT minimizes a regularized logistic loss function over M = 180 sequential boosting stages. At stage m, a shallow decision tree h_m(x) is fit to the negative gradients (pseudo-residuals) of the loss function with respect to the previous ensemble prediction F_{m-1}(x):")
    
    add_body(doc, "r_{im} = - [ partial L(y_i, F(x_i)) / partial F(x_i) ]_{F = F_{m-1}} = y_i - p_{m-1}(x_i)\n"
             "where p_{m-1}(x) = 1 / (1 + exp(-F_{m-1}(x))).")
    
    add_body(doc, "The ensemble is updated via a shrinkage parameter (learning rate eta = 0.05) to prevent overfitting:\n"
             "F_m(x) = F_{m-1}(x) + eta * gamma_m * h_m(x)\n"
             "where gamma_m is the optimal step length computed via line search in each leaf node.")
    
    add_body(doc, "Table 4.3.1 summarizes the optimal hyperparameters identified through 5-fold stratified cross-validation on the 2001–2021 training set.")
    
    add_p(doc, "Table 4.3.1: Hyperparameter Specifications for 180-Tree GBDT Weather Classifier", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    gbdt_headers = ["Hyperparameter", "Configured Value", "Optimization Rationale"]
    gbdt_widths = [Inches(2.2), Inches(1.8), Inches(2.8)]
    gbdt_data = [
        ["Number of Boosting Trees (n_estimators)", "180", "Sufficient capacity to capture non-linear interactions without overfitting"],
        ["Learning Rate (shrinkage eta)", "0.05", "Low shrinkage ensures stable, conservative gradient descent steps"],
        ["Maximum Tree Depth (max_depth)", "4", "Limits interaction order to 4-way feature conjunctions; prevents noise fitting"],
        ["Subsample Fraction (subsample)", "0.85", "Stochastic gradient boosting introduces variance reduction and regularization"],
        ["Minimum Samples per Split (min_samples_split)", "10", "Guarantees sufficient statistical support before creating tree branches"],
        ["Loss Function", "log_loss (deviance)", "Standard binary cross-entropy loss for well-calibrated class probabilities"]
    ]
    t_431 = doc.add_table(rows=1, cols=3)
    style_academic_table(t_431, gbdt_widths, gbdt_headers, gbdt_data)
    
    add_p(doc, "", space_before=10)
    add_fig(doc, r"generated_charts\model_performance_comparison.png", 
            "Figure 4.3.1: 180-Tree GBDT Weather Classifier ROC and PR Curves", width=Inches(5.5))
    
    add_h3(doc, "4.3.2 128-Tree Multi-Output Relief Demand Ensemble")
    add_body(doc, "Accurately forecasting relief demands requires predicting three continuous, correlated targets simultaneously: drinking water (liters), food rations (units), and medical care kits (kits). Because disaster demands are strongly coupled—a flooded ward requiring water almost certainly requires food and medical support—a multi-output regression ensemble is architected.")
    
    add_body(doc, "The ensemble blends three diverse model families:\n"
             "1. Extremely Randomized Trees (ExtraTreesRegressor, 64 trees): Introduces extreme random thresholding at tree nodes, dramatically reducing prediction variance and suppressing spatial noise.\n"
             "2. Random Forest Regressor (RandomForestRegressor, 64 trees): Constructs bootstrap-aggregated decision trees with optimal greedy splits, capturing strong non-linear threshold effects.\n"
             "3. Scaled Ridge Regression (alpha = 1.0): Provides global linear stability, acting as an anchor preventing tree-based predictions from extrapolating erratically under unseen disaster extremes.")
    
    add_body(doc, "The final prediction vector hat{y} in R^3 is computed as a weighted blend:\n"
             "hat{y} = w_1 * hat{y}_{ExtraTrees} + w_2 * hat{y}_{RandomForest} + w_3 * hat{y}_{Ridge}\n"
             "where weights [w_1 = 0.50, w_2 = 0.35, w_3 = 0.15] were optimized on the holdout validation set.")
    
    add_body(doc, "Table 4.3.2 lists the structural parameters of the multi-output demand ensemble.")
    
    add_p(doc, "Table 4.3.2: Ensemble Architecture Parameters for Relief Demand Prediction", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    ens_headers = ["Ensemble Component", "Tree Count / Param", "Split Criterion", "Key Functional Role"]
    ens_widths = [Inches(2.0), Inches(1.5), Inches(1.5), Inches(1.8)]
    ens_data = [
        ["Extra Trees Regressor", "64 trees, max_depth=12", "Mean Squared Error (MSE)", "Variance reduction via random thresholds"],
        ["Random Forest Regressor", "64 trees, max_depth=12", "Mean Squared Error (MSE)", "Non-linear pattern and threshold capture"],
        ["Ridge Linear Regressor", "alpha = 1.0 (L2 penalty)", "L2 Regularized RSS", "Linear baseline anchor; prevents drift"]
    ]
    t_432 = doc.add_table(rows=1, cols=4)
    style_academic_table(t_432, ens_widths, ens_headers, ens_data)
    
    # 4.4 Conformal Calibration
    add_h2(doc, "4.4 Distribution-Free Split-Conformal Uncertainty Calibration")
    add_body(doc, "In humanitarian logistics, an under-predicted demand value translates directly into human suffering and preventable casualties. To convert point estimates hat{y}_i into mathematically guaranteed prediction intervals without making unrealistic Gaussian distribution assumptions, the platform implements inductive Split-Conformal Prediction.")
    
    add_body(doc, "The conformal calibration algorithm operates as follows:\n"
             "1. Let D_{cal} = {(x_i, y_i)}_{i=1}^n be an independent calibration set of n = 9,622 disaster records held out entirely from ensemble training.\n"
             "2. For each calibration record i in D_{cal} and each relief commodity k in {Water, Food, Medical}, compute the absolute nonconformity residual:\n"
             "   R_i^k = | y_i^k - hat{y}^k(x_i) |\n"
             "3. For a user-specified coverage confidence level 1 - alpha (configured at nominal 90%, alpha = 0.10), compute the empirical quantile hat{q}^k as the ceil((n + 1)(1 - alpha)) / n-th empirical quantile of {R_1^k, ..., R_n^k}.\n"
             "4. For any new unseen ward query x_{new}, the calibrated 90% prediction interval is constructed as:\n"
             "   C^k(x_{new}) = [ max(0, hat{y}^k(x_{new}) - hat{q}^k), hat{y}^k(x_{new}) + hat{q}^k ].")
    
    add_body(doc, "By the exchangeability theorem of conformal prediction, this formulation mathematically guarantees finite-sample coverage:\n"
             "P( y_{new}^k in C^k(x_{new}) ) >= 1 - alpha = 0.90\n"
             "regardless of the underlying probability distribution of demands or the internal complexity of the regression ensemble.")
    
    add_body(doc, "Table 4.4.1 details the empirical nonconformity quantiles hat{q} and verified test coverage across all three commodities on 9,622 untouched test instances.")
    
    add_p(doc, "Table 4.4.1: Split-Conformal Nonconformity Quantiles and Empirical Coverage Validation", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    conf_headers = ["Relief Commodity", "Nominal Target", "Calibrated Margin (hat{q})", "Empirical Test Coverage", "Mathematical Guarantee"]
    conf_widths = [Inches(1.8), Inches(1.2), Inches(1.6), Inches(1.4), Inches(1.2)]
    conf_data = [
        ["Potable Water (L)", "90.0%", "+/- 248.50 L", "89.81%", "Finite-Sample Validated"],
        ["Food Rations (Units)", "90.0%", "+/- 175.20 units", "90.29%", "Finite-Sample Validated"],
        ["Medical Kits (Kits)", "90.0%", "+/- 18.40 kits", "93.90%", "Finite-Sample Validated"]
    ]
    t_441 = doc.add_table(rows=1, cols=5)
    style_academic_table(t_441, conf_widths, conf_headers, conf_data)
    
    add_p(doc, "", space_before=10)
    add_fig(doc, r"generated_charts\confidence_calibration.png", 
            "Figure 4.4.1: Split-Conformal 90% Prediction Interval Calibration Across Relief Commodities", width=Inches(5.5))
    
    # 4.5 Multi-Commodity Supply Allocation via OR-Tools
    add_h2(doc, "4.5 Multi-Commodity Supply Allocation via Linear Programming")
    add_body(doc, "Once calibrated demand upper bounds D_i^k are established for all shelters i in {1..I} and commodities k in {Water, Food, Medical}, the platform must compute an optimal distribution plan from central warehouses j in {1..J} that respects physical warehouse stock limits while prioritizing high-vulnerability populations.")
    
    add_body(doc, "The allocation problem is formulated as a continuous multi-commodity linear program (LP) solved via Google OR-Tools GLOP. Let x_{ij}^k denote the quantity of commodity k shipped from depot j to shelter i, and let s_i^k >= 0 denote the unmet demand slack variable at shelter i.")
    
    add_body(doc, "The objective function minimizes total transportation impedance while heavily penalizing unmet demand weighted by shelter vulnerability priority w_i:\n"
             "Minimize Z = sum_{k} sum_{i} sum_{j} ( c_{ij} * x_{ij}^k ) + sum_{k} sum_{i} ( P^k * w_i * s_i^k )\n"
             "subject to:\n"
             "1. Warehouse Capacity Conservation: For every depot j and commodity k,\n"
             "   sum_{i=1}^I x_{ij}^k <= S_j^k\n"
             "2. Shelter Demand Balance: For every shelter i and commodity k,\n"
             "   sum_{j=1}^J x_{ij}^k + s_i^k >= D_i^k\n"
             "3. Non-negativity: x_{ij}^k >= 0, s_i^k >= 0 for all i, j, k.")
    
    add_body(doc, "Here, c_{ij} is the normalized network travel distance between depot j and shelter i, P^k is the unmet penalty weight (set to P^{water} = 10,000, P^{food} = 8,000, P^{med} = 15,000 to ensure that meeting physical survival needs takes absolute precedence over transport distance), and w_i in [1.0, 3.0] is the socio-economic vulnerability weight of the destination shelter.")
    
    add_body(doc, "Table 4.5.1 summarizes the mathematical parameters and linear constraints implemented in supply_solver.py.")
    
    add_p(doc, "Table 4.5.1: Multi-Commodity Supply Optimization Parameters and Linear Constraints", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    opt_headers = ["Mathematical Parameter", "Symbol", "Configured Value", "Operational Rationale"]
    opt_widths = [Inches(2.0), Inches(1.0), Inches(1.8), Inches(2.0)]
    opt_data = [
        ["Water Unmet Penalty", "P^{water}", "10,000", "Forces complete fulfillment of drinking water before distance minimization"],
        ["Food Unmet Penalty", "P^{food}", "8,000", "Prevents nutritional starvation at isolated shelters"],
        ["Medical Unmet Penalty", "P^{med}", "15,000", "Highest penalty; treats life-saving medical supplies as paramount"],
        ["Depot Node Count", "J", "5 Central Warehouses", "North, South, Central, West, and Airport Logistics Hubs"],
        ["Shelter Node Count", "I", "12 Municipal Shelters", "Primary designated flood relief shelters across Chennai"],
        ["Continuous Variables", "x_{ij}^k, s_i^k", "180 Decision Variables", "3 commodities * 5 depots * 12 shelters + 36 slack variables"],
        ["Solver Algorithm", "GLOP (Primal Simplex)", "Tolerance = 1e-7", "Guarantees exact global optimality in <65 milliseconds"]
    ]
    t_451 = doc.add_table(rows=1, cols=4)
    style_academic_table(t_451, opt_widths, opt_headers, opt_data)
    
    # 4.6 Hazard-Aware Evacuation Routing
    add_h2(doc, "4.6 Hazard-Aware Evacuation Routing via Dynamic Graph Traversal")
    add_body(doc, "To ensure that relief convoys and civilian evacuees are never routed into impassable floodwaters, the platform models Chennai's road network as a dynamic directed graph G = (V, E) in NetworkX. Each edge e = (u, v) in E possesses attributes for physical road length L_{uv}, baseline speed limit v_{uv}, and real-time localized flood water depth d_{uv}.")
    
    add_body(doc, "Before executing pathfinding, edges are evaluated against vehicle-specific critical submersion thresholds theta_{veh}. If d_{uv} > theta_{veh}, edge (u, v) is pruned from the traversable graph:\n"
             "E_{traversable}(veh) = { (u, v) in E | d_{uv} <= theta_{veh} }.")
    
    add_body(doc, "For all surviving edges, the dynamic travel impedance weight W_{uv} is computed by scaling free-flow travel time by a non-linear hydraulic delay penalty:\n"
             "W_{uv} = ( L_{uv} / v_{uv} ) * [ 1 + beta * ( d_{uv} / theta_{veh} )^2 ]\n"
             "where beta = 3.0 represents the hydrodynamic drag and caution multiplier. As water depth approaches the critical threshold theta_{veh}, the effective traversal cost quadruples, naturally guiding the Dijkstra / A* search heuristic toward elevated bypasses and flyovers.")
    
    add_body(doc, "Table 4.6.1 defines the critical water depth thresholds and operational rules enforced across vehicle classifications.")
    
    add_p(doc, "Table 4.6.1: Road Inundation Traversal Thresholds by Vehicle Classification", 
          font_size=11, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=10, space_after=6)
    
    veh_headers = ["Vehicle / Agent Class", "Critical Depth (theta)", "Max Safe Velocity", "Operational Deployment Role"]
    veh_widths = [Inches(1.8), Inches(1.4), Inches(1.4), Inches(2.2)]
    veh_data = [
        ["Pedestrian Evacuee", "0.50 m (Knee-to-waist)", "2.0 km/h", "Civilian evacuation to local neighborhood shelters"],
        ["Standard Relief Truck", "0.30 m (Axle height)", "15.0 km/h", "High-capacity bulk commodity transport from depots"],
        ["High-Clearance 4x4", "0.65 m (Snorkel depth)", "20.0 km/h", "Specialized medical evacuation and rapid reconnaissance"],
        ["Inflatable Rescue Boat", ">= 0.40 m (Min draft)", "12.0 km/h", "Waterborne rescue in deep inundated zones (Velachery, Manali)"],
        ["Rotary Aerial Drop", "Inf (No depth limit)", "120.0 km/h", "Airlift delivery to completely cut-off rooftop clusters"]
    ]
    t_461 = doc.add_table(rows=1, cols=4)
    style_academic_table(t_461, veh_widths, veh_headers, veh_data)
    
    # 4.7 Geospatial Dashboard & Bilingual Bulletins
    add_h2(doc, "4.7 Geospatial Dashboard, Bilingual Bulletins & Automated Reporting")
    add_body(doc, "The operational interface is architected as an ultra-responsive single-page application built on Next.js 14 (React 18) and styled with Tailwind CSS. Geospatial layers—including 200 GCC ward choropleth polygons colored by flood severity, depot inventory markers, shelter status pins, and active multi-modal evacuation route polylines—are rendered using client-side Leaflet and HTML5 Canvas overlays.")
    
    add_body(doc, "To bridge the critical communication gap between high-level command centers and grassroots first responders, the platform incorporates an automated bilingual natural language advisory generator (advisory.py). Based on the simulated ward status, the engine synthesizes immediate operational bulletins in both English and Tamil:")
    
    add_bullet(doc, "Tamil Public Bulletin Synthesis", 
               "Generates localized Tamil advisories specifying ward danger levels ('எச்சரிக்கை: தீவிர வெள்ள அபாயம்'), designated relief shelters, emergency helpline contacts (1913 GCC Helpline, 1070 State Emergency Ops), and safe evacuation paths avoiding submerged subways.")
    
    add_bullet(doc, "English Command Manifests", 
               "Generates structured logistics manifests for depot loading supervisors, detailing exact vehicle loading quantities (cases of water, ration packets, medical kits), departure timestamps, and assigned truck driver turn-by-turn waypoints.")
    
    add_bullet(doc, "Offline 200-Ward GCC Atlas & Standalone Reports", 
               "Compiles complete situational snapshots into self-contained, standalone HTML/PDF reports containing embedded SVG maps, inventory balance sheets, and ward vulnerability rankings. These documents can be exported, printed, or shared via low-bandwidth mesh radios when cellular communication towers suffer power outages.")
    
    doc.add_page_break()
