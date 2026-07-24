from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/evaluations", tags=["RAG Evaluations"])


@router.get("/report")
def get_evaluation_report():
    """
    Get the latest automated RAG evaluation benchmark report metrics.
    """
    report_path = Path("data/eval_report.md")
    dataset_path = Path("data/eval_dataset.json")

    report_md = ""
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as f:
            report_md = f.read()

    queries_count = 0
    if dataset_path.exists():
        import json
        with open(dataset_path, "r", encoding="utf-8") as f:
            queries_count = len(json.load(f))

    return {
        "status": "success",
        "benchmark_queries_count": queries_count,
        "report_file": str(report_path),
        "report_markdown": report_md or "Evaluation report not generated yet. Run `python -m scripts.run_evaluations` to build."
    }
