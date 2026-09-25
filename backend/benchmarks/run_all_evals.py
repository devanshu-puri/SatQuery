import os
import sys
import json
import time

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from benchmarks.eval_vrsbench import run_vrsbench_eval
from benchmarks.eval_rsvqa import run_rsvqa_eval
from benchmarks.eval_cdvqa import run_cdvqa_eval

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "eval_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_all_benchmarks():
    print("#" * 75)
    print("SATQUERY AI — FULL BENCHMARK SUITE EVALUATION")
    print("#" * 75)
    start_time = time.time()

    vrs_res = run_vrsbench_eval()
    rsvqa_res = run_rsvqa_eval()
    cdvqa_res = run_cdvqa_eval()

    total_time = round(time.time() - start_time, 2)
    total_test_cases = vrs_res["total_examples"] + rsvqa_res["total_examples"] + cdvqa_res["total_examples"]

    summary = {
        "status": "COMPLETED",
        "total_benchmarks_evaluated": 3,
        "total_test_cases_evaluated": total_test_cases,
        "total_evaluation_time_seconds": total_time,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "benchmarks": {
            "vrsbench": {
                "name": "VRSBench Official Test Split",
                "sample_size": vrs_res["total_examples"],
                "overall_accuracy_pct": round(vrs_res["overall_accuracy"] * 100, 2),
                "vqa_accuracy_pct": vrs_res["metrics"]["vqa_accuracy"],
                "captioning_token_f1_pct": vrs_res["metrics"]["captioning_token_f1"],
                "grounding_acc_at_50_iou_pct": vrs_res["metrics"]["grounding_acc_at_50_iou"],
                "mean_latency_ms": vrs_res["mean_latency_ms"],
                "raw_receipt_file": "vrsbench_result.json"
            },
            "rsvqa": {
                "name": "RSVQA-LR/HR Official Test Split",
                "sample_size": rsvqa_res["total_examples"],
                "overall_accuracy_pct": rsvqa_res["overall_accuracy"],
                "category_accuracy": rsvqa_res["category_accuracy"],
                "mean_latency_ms": rsvqa_res["mean_latency_ms"],
                "raw_receipt_file": "rsvqa_result.json"
            },
            "cdvqa": {
                "name": "CDVQA Bi-Temporal Change-VQA Official Test Split",
                "sample_size": cdvqa_res["total_examples"],
                "overall_accuracy_pct": cdvqa_res["overall_accuracy"],
                "category_accuracy": cdvqa_res["category_accuracy"],
                "mean_latency_ms": cdvqa_res["mean_latency_ms"],
                "raw_receipt_file": "cdvqa_result.json"
            }
        }
    }

    summary_file = os.path.join(RESULTS_DIR, "benchmark_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "#" * 75)
    print("ALL BENCHMARK EVALUATIONS COMPLETED SUCCESSFULLY!")
    print(f"Total Test Cases Run: {total_test_cases} in {total_time}s")
    print(f"Summary JSON saved: {summary_file}")
    print("#" * 75)
    return summary

if __name__ == "__main__":
    run_all_benchmarks()
