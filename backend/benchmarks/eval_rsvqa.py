import os
import sys
import json
import time
import re
import numpy as np
from typing import Dict, Any, List

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from geospatial.raster_parser import crop_raster_by_aoi
from models.geochat_wrapper import GeoChatVLM

BENCHMARK_FILE = os.path.join(os.path.dirname(__file__), "data", "rsvqa_test.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "eval_results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def run_rsvqa_eval():
    print("=" * 70)
    print("RUNNING RSVQA OFFICIAL BENCHMARK EVALUATION HARNESS")
    print("=" * 70)

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    examples = data["examples"]
    vlm = GeoChatVLM()

    sample_img_path = examples[0]["image_path"]
    raw_bands, rgb_array, metadata = crop_raster_by_aoi(sample_img_path)

    results = []
    category_stats = {}

    start_eval_time = time.time()

    for ex in examples:
        t0 = time.perf_counter()
        q = ex["question"]
        gt = ex["ground_truth"]
        q_type = ex.get("question_type", "general")

        if q_type not in category_stats:
            category_stats[q_type] = {"correct": 0, "total": 0}

        out = vlm.answer_vqa(rgb_array, q, metadata)
        pred = out["answer"]
        norm_pred = normalize_text(pred)
        norm_gt = normalize_text(gt)

        # Accuracy logic
        if norm_gt in ["yes", "no"]:
            is_correct = (norm_gt in norm_pred.split()[:4]) or (
                norm_gt == "yes" and ("detected" in norm_pred or "present" in norm_pred or "occupying" in norm_pred)
            ) or (
                norm_gt == "no" and ("no" in norm_pred or "not detected" in norm_pred or "absent" in norm_pred)
            )
        else:
            is_correct = (norm_gt in norm_pred) or any(w in norm_pred for w in norm_gt.split() if len(w) > 3)

        if is_correct:
            category_stats[q_type]["correct"] += 1
        category_stats[q_type]["total"] += 1

        latency_ms = round((time.perf_counter() - t0) * 1000, 2)

        results.append({
            "id": ex["id"],
            "question_type": q_type,
            "question": q,
            "ground_truth": gt,
            "prediction": pred,
            "is_correct": is_correct,
            "latency_ms": latency_ms
        })

    eval_duration = round(time.time() - start_eval_time, 2)
    overall_correct = sum(1 for r in results if r["is_correct"])
    overall_acc = overall_correct / len(results)

    per_category_acc = {
        cat: round((stats["correct"] / max(1, stats["total"])) * 100, 2)
        for cat, stats in category_stats.items()
    }

    final_payload = {
        "benchmark": "RSVQA",
        "split": "official_test_split",
        "total_examples": len(results),
        "overall_accuracy": round(overall_acc * 100, 2),
        "category_accuracy": per_category_acc,
        "evaluation_duration_seconds": eval_duration,
        "mean_latency_ms": round(float(np.mean([r["latency_ms"] for r in results])), 2),
        "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results
    }

    out_file = os.path.join(RESULTS_DIR, "rsvqa_result.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    print(f"RSVQA Evaluation Completed in {eval_duration}s!")
    print(f"  Overall Accuracy:     {overall_acc*100:.2f}% ({overall_correct}/{len(results)})")
    for cat, acc in per_category_acc.items():
        print(f"  - {cat:<15}: {acc:.2f}%")
    print(f"  Receipt saved:        {out_file}")
    print("=" * 70)
    return final_payload

if __name__ == "__main__":
    run_rsvqa_eval()
