"""Expose reproducible evaluation evidence without running training in an HTTP request."""
import hashlib
import json
from pathlib import Path
from fastapi import APIRouter, Request

router = APIRouter()
PIPELINE = Path(__file__).parents[2] / "ml_pipeline"


def load_verified_report(root=PIPELINE, predictor=None):
    try:
        report = json.loads((root / "models/runtime_evaluation.json").read_text(encoding="utf-8"))
        if not isinstance(report, dict):
            return None
        from backend.app.services.demand_predictor import DemandPredictor
        predictor = predictor or DemandPredictor(root / 'models' / report.get('artifact_name', 'demand_forest.json'))
        if not predictor.is_loaded or report.get('model_sha256') != predictor.model_sha256:
            return None
        for key, path in (("model_sha256", predictor.path),
                          ("dataset_sha256", "dataset/chennai_historical_2015_2023.csv")):
            if report.get(key) != hashlib.sha256((root / path).read_bytes()).hexdigest():
                return None
        if not report.get("rows") or report.get("ml_rows", 0) + report.get("rule_fallback_rows", 0) != report["rows"]:
            return None
        return report
    except (OSError, ValueError, TypeError):
        return None


@router.get("/model/evaluation")
def model_evaluation(request: Request):
    predictor = request.app.state.ml_predictor
    metadata = predictor.metadata() if hasattr(predictor, "metadata") else {"name": "Legacy ensemble"}
    # This report evaluates the portable artifact, not an optional legacy model.
    from backend.app.services.demand_predictor import DemandPredictor
    report = load_verified_report(predictor=predictor) if isinstance(predictor, DemandPredictor) and predictor.is_loaded else None
    return {
        "model": metadata,
        "evaluation": report,
        "evaluation_status": "verified" if report else "unavailable_or_stale",
        "reproduce_command": "python -m backend.ml_pipeline.evaluate_portable_model --save",
        "limitations": ["Training and evaluation labels are synthetic.",
                        "Relief demand is predicted; flood extent and depth use scenario calculations.",
                        "Held-out synthetic errors do not establish accuracy on observed floods.",
                        "Coverage is marginal per resource, not a guarantee for a new event."],
    }
