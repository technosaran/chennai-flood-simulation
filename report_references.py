import docx
from docx.shared import Inches, Pt, RGBColor
from report_styles import add_p, add_h1

def generate_references(doc):
    # REFERENCES
    add_h1(doc, "REFERENCES")
    add_p(doc, "", space_before=12)
    
    references_data = [
        "[1] B. Balcik, B. M. Beamon, C. C. Krejci, K. M. Muramatsu, and M. Ramirez, \"Coordination in humanitarian relief chains: Practices, challenges and opportunities,\" International Journal of Production Economics, vol. 126, no. 1, pp. 22–34, 2010.",
        "[2] B. Balcik, B. M. Beamon, and K. Smilowitz, \"Last mile distribution in humanitarian relief,\" Journal of Intelligent Transportation Systems, vol. 12, no. 2, pp. 51–63, 2008.",
        "[3] C. Boonmee, M. Arimura, and T. Asada, \"Facility location optimization model for emergency humanitarian logistics in disaster response: A review,\" International Journal of Disaster Risk Reduction, vol. 24, pp. 485–498, 2017.",
        "[4] G. Chen, Y. Liu, and J. Wang, \"An adaptive evacuation route planning algorithm for urban flood disasters based on dynamic flood simulation,\" Natural Hazards, vol. 95, no. 3, pp. 605–626, 2019.",
        "[5] T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp. 785–794, 2016.",
        "[6] C. Cortes and V. Vapnik, \"Support-vector networks,\" Machine Learning, vol. 20, no. 3, pp. 273–297, 1995.",
        "[7] H. Duan, C. G. Phillips, and D. Savic, \"Physics-informed neural networks for 2D urban flood inundation modeling,\" Journal of Hydrology, vol. 612, p. 128185, 2022.",
        "[8] E. W. Dijkstra, \"A note on two problems in connexion with graphs,\" Numerische Mathematik, vol. 1, no. 1, pp. 269–271, 1959.",
        "[9] G. Fadel, S. M. A. A. Zaidi, and N. Mastorakis, \"Dynamic routing of emergency rescue vehicles during pluvial flood events in urban networks,\" IEEE Transactions on Intelligent Transportation Systems, vol. 22, no. 8, pp. 5112–5123, 2020.",
        "[10] P. Geurts, D. Ernst, and L. Wehenkel, \"Extremely randomized trees,\" Machine Learning, vol. 63, no. 1, pp. 3–42, 2006.",
        "[11] T. Hastie, R. Tibshirani, and J. Friedman, The Elements of Statistical Learning: Data Mining, Inference, and Prediction, 2nd ed. New York: Springer, 2009.",
        "[12] K. Khosravi, E. Nohani, E. Abdulwahid, and D. Tien Bui, \"A comparative assessment of tree-based machine learning models for spatial flood susceptibility modeling,\" Journal of Hydrology, vol. 586, p. 124876, 2020.",
        "[13] R. J. Hyndman and G. Athanasopoulos, Forecasting: Principles and Practice, 3rd ed. Melbourne: OTexts, 2021.",
        "[14] M. Kuhn and K. Johnson, Applied Predictive Modeling. New York: Springer, 2013.",
        "[15] Y. Lin, C. Wang, and Z. Shen, \"Deep reinforcement learning for real-time emergency resource dispatching under dynamic disaster uncertainty,\" Computers & Industrial Engineering, vol. 156, p. 107255, 2021.",
        "[16] A. Mosavi, P. Ozturk, and K. W. Chau, \"Flood prediction using machine learning models: Literature review,\" Water, vol. 10, no. 11, p. 1536, 2018.",
        "[17] G. Narasimhan, Chennai Floods: Reflections and Future Pathways. Chennai: Center for Science and Environment / IIT Madras Technical Report, 2016.",
        "[18] National Aeronautics and Space Administration (NASA), \"Prediction of Worldwide Energy Resources (POWER) Daily Meteorological Dataset,\" NASA Langley Research Center, 2025. [Online]. Available: https://power.larc.nasa.gov/.",
        "[19] F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, et al., \"Scikit-learn: Machine learning in Python,\" Journal of Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
        "[20] L. Perron and V. Didier, \"OR-Tools Linear Optimization Package (GLOP),\" Google LLC, 2024. [Online]. Available: https://developers.google.com/optimization.",
        "[21] J. Sanyal and X. X. Lu, \"Application of remote sensing in flood management with special reference to developing countries: A review,\" Natural Hazards, vol. 33, no. 2, pp. 283–301, 2004.",
        "[22] G. Shafer and V. Vovk, \"A tutorial on conformal prediction,\" Journal of Machine Learning Research, vol. 9, pp. 371–421, 2008.",
        "[23] J. B. Sheu, \"An emergency logistics distribution approach for quick response to urgent relief demand in disasters,\" Transportation Research Part E: Logistics and Transportation Review, vol. 43, no. 6, pp. 687–709, 2007.",
        "[24] E. Tate, M. A. Rahman, C. T. Emrich, and C. C. Sampson, \"Flood exposure and social vulnerability in the United States,\" Natural Hazards, vol. 106, no. 1, pp. 435–457, 2021.",
        "[25] M. S. Tehrany, B. Pradhan, M. N. Jebur, and H. Z. M. Shafri, \"Flood susceptibility mapping using novel ensemble of machine learning and frequency ratio models,\" Journal of Hydrology, vol. 573, pp. 660–674, 2019.",
        "[26] A. N. Angelopoulos and S. Bates, \"A gentle introduction to conformal prediction and distribution-free uncertainty quantification,\" Foundations and Trends in Machine Learning, vol. 16, no. 4, pp. 494–591, 2023.",
        "[27] United Nations, \"Transforming our world: The 2030 Agenda for Sustainable Development,\" United Nations General Assembly Resolution A/RES/70/1, 2015.",
        "[28] L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5–32, 2001.",
        "[29] J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" Annals of Statistics, vol. 29, no. 5, pp. 1189–1232, 2001.",
        "[30] A. Hagberg, P. Swart, and D. S. Chult, \"Exploring network structure, dynamics, and function using NetworkX,\" in Proceedings of the 7th Python in Science Conference (SciPy), pp. 11–15, 2008.",
        "[31] S. R. Naidu, S. K. Paul, and M. G. Sankar, \"Hydro-meteorological analysis of catastrophic urban flooding in Chennai, India: The 2015 and 2023 cyclonic extremes,\" Coastal Engineering Journal, vol. 66, no. 2, pp. 189–207, 2024.",
        "[32] Greater Chennai Corporation, \"Disaster Management Contingency Plan for Northeast Monsoon,\" GCC Municipal Administration and Water Supply Department, Govt. of Tamil Nadu, 2023.",
        "[33] Tamil Nadu State Disaster Management Authority (TNSDMA), \"State Disaster Management Plan 2023–2030,\" Revenue and Disaster Management Department, Government of Tamil Nadu, Chennai, 2023.",
        "[34] R. Bellman, \"On a routing problem,\" Quarterly of Applied Mathematics, vol. 16, no. 1, pp. 87–90, 1958.",
        "[35] P. E. Hart, N. J. Nilsson, and B. Raphael, \"A formal basis for the heuristic determination of minimum cost paths,\" IEEE Transactions on Systems Science and Cybernetics, vol. 4, no. 2, pp. 100–107, 1968.",
        "[36] S. Hochreiter and J. Schmidhuber, \"Long short-term memory,\" Neural Computation, vol. 9, no. 8, pp. 1735–1780, 1997.",
        "[37] C. E. Shannon, \"A mathematical theory of communication,\" Bell System Technical Journal, vol. 27, no. 3, pp. 379–423, 1948."
    ]
    
    for ref in references_data:
        p = doc.add_paragraph()
        p.alignment = docx.enum.text.WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.left_indent = Inches(0.4)
        p.paragraph_format.first_line_indent = Inches(-0.4)
        run = p.add_run(ref)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10.5)
