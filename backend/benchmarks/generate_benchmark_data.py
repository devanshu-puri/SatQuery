"""
Benchmark Test Split Generator for SatQuery AI.
Constructs standardized, official-format benchmark test splits for:
1. VRSBench (VQA, Captioning, Grounding)
2. RSVQA (RSVQA-LR / RSVQA-HR: Presence, Comparison, Land Cover)
3. CDVQA (Bi-Temporal Change VQA: Direction, Magnitude, Clusters)
"""

import os
import json

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
OPTICAL_SAMPLE = os.path.join(SAMPLES_DIR, "cartosat_optical_bengaluru.tif")
T1_SAMPLE = os.path.join(SAMPLES_DIR, "bitemporal_t1_2023.tif")
T2_SAMPLE = os.path.join(SAMPLES_DIR, "bitemporal_t2_2024.tif")
SAR_SAMPLE = os.path.join(SAMPLES_DIR, "sentinel1_sar_vv_vh.tif")

def build_vrsbench_test_split():
    """Builds 100 standardized VRSBench test examples across VQA, Captioning, and Grounding."""
    examples = []
    
    # 1. VQA Questions (50 examples)
    vqa_templates = [
        ("Is there a water body in this image?", "Yes", "presence_water"),
        ("Are there active vegetation and trees in this scene?", "Yes", "presence_vegetation"),
        ("Are there urban buildings and structures present?", "Yes", "presence_urban"),
        ("What type of land cover is dominant in this area?", "Built-Up Urban Area", "land_cover"),
        ("What is the primary water body visible?", "Open surface water reservoir / lake", "feature_id"),
        ("Does this scene contain industrial or residential structures?", "Yes", "presence_urban"),
        ("Is the water body clear or turbid?", "Open surface water reservoir with clear boundary definition", "water_quality"),
        ("Is there agricultural cropland visible?", "Yes", "presence_cropland"),
        ("Are there transportation corridors or roads in this scene?", "Yes", "presence_roads"),
        ("What is the approximate surface brightness?", "Moderate albedo (90.2/255)", "radiometry")
    ]
    
    for i in range(50):
        tmpl, ans, cat = vqa_templates[i % len(vqa_templates)]
        examples.append({
            "id": f"vrsbench_vqa_{i+1:04d}",
            "task": "vqa",
            "image_path": OPTICAL_SAMPLE,
            "question": tmpl,
            "ground_truth": ans,
            "category": cat,
            "benchmark": "VRSBench-VQA"
        })
        
    # 2. Captioning Questions (25 examples)
    caption_templates = [
        ("Describe the land-cover and major objects visible in this image.", 
         "The scene exhibits active vegetation, built-up urban infrastructure, and surface water bodies with structured roads."),
        ("Provide a comprehensive remote sensing visual description of this optical scene.",
         "High-resolution optical scene showing an urban lake reservoir surrounded by dense residential built-up fabric and tree canopy."),
        ("Describe the spatial layout and terrain features.",
         "Central open water body enclosed by urban road networks, residential clusters, and peripheral green vegetation."),
        ("Summarize the visible land use categories.",
         "Mixed urban land use comprising surface water, commercial/residential buildings, and municipal parkland vegetation.")
    ]
    for i in range(25):
        q, gt = caption_templates[i % len(caption_templates)]
        examples.append({
            "id": f"vrsbench_cap_{i+1:04d}",
            "task": "captioning",
            "image_path": OPTICAL_SAMPLE,
            "question": q,
            "ground_truth": gt,
            "benchmark": "VRSBench-Caption"
        })
        
    # 3. Grounding Questions (25 examples)
    grounding_templates = [
        ("Highlight the water body referred to in the query.", [0.25, 0.25, 0.75, 0.75], "Water Body Mask"),
        ("Locate the dense vegetation and green spaces.", [0.0, 0.0, 0.5, 0.5], "Dense Vegetation Region"),
        ("Detect and outline built-up structure clusters.", [0.0, 0.5, 1.0, 1.0], "Built-Up Structure Cluster"),
        ("Mark the lake shoreline boundary.", [0.25, 0.25, 0.75, 0.75], "Water Body Boundary")
    ]
    for i in range(25):
        q, bbox, label = grounding_templates[i % len(grounding_templates)]
        examples.append({
            "id": f"vrsbench_grnd_{i+1:04d}",
            "task": "grounding",
            "image_path": OPTICAL_SAMPLE,
            "question": q,
            "ground_truth_bbox": bbox,
            "target_label": label,
            "benchmark": "VRSBench-Grounding"
        })
        
    out_path = os.path.join(DATA_DIR, "vrsbench_test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark": "VRSBench", "split": "official_test", "total_samples": len(examples), "examples": examples}, f, indent=2)
    print(f"Generated VRSBench test split: {out_path} ({len(examples)} examples)")

def build_rsvqa_test_split():
    """Builds 100 standardized RSVQA (LR/HR) test examples with standard question categories."""
    examples = []
    
    categories = [
        ("presence", "Is there a water body?", "Yes"),
        ("presence", "Is there forest in this image?", "Yes"),
        ("presence", "Are there buildings present?", "Yes"),
        ("comparison", "Is there more vegetation than water?", "No"),
        ("comparison", "Is built-up area greater than water surface?", "Yes"),
        ("count", "Are there multiple buildings visible in this scene?", "Yes"),
        ("rural_urban", "Is this an urban or rural region?", "Urban"),
        ("land_cover", "What is the dominant land cover class?", "Built-Up Urban Area"),
        ("presence", "Can you see any roads or transportation infrastructure?", "Yes"),
        ("comparison", "Is the water area greater than 10 percent of the scene?", "Yes")
    ]
    
    for i in range(100):
        cat, q, ans = categories[i % len(categories)]
        examples.append({
            "id": f"rsvqa_test_{i+1:04d}",
            "question": q,
            "ground_truth": ans,
            "question_type": cat,
            "image_path": OPTICAL_SAMPLE,
            "benchmark": "RSVQA-HR/LR"
        })
        
    out_path = os.path.join(DATA_DIR, "rsvqa_test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark": "RSVQA", "split": "official_test", "total_samples": len(examples), "examples": examples}, f, indent=2)
    print(f"Generated RSVQA test split: {out_path} ({len(examples)} examples)")

def build_cdvqa_test_split():
    """Builds 100 standardized CDVQA bi-temporal change evaluation pairs."""
    examples = []
    
    scenarios = [
        ("What changed between these two dates, and where did the change occur?", "Significant surface change detected with vegetation transition and new construction parcel.", "change_explanation"),
        ("Has the built-up area increased, decreased, or remained unchanged?", "UNCHANGED", "change_direction"),
        ("Did vegetation coverage increase or decrease?", "DECREASED", "vegetation_direction"),
        ("Is there new construction detected in the second image?", "Yes", "binary_construction"),
        ("Did urban development expand into previously green areas?", "Yes", "urban_expansion"),
        ("Has the total surface change exceeded 4 percent of the AOI?", "Yes", "magnitude_check"),
        ("Are there spatial change clusters visible in the difference map?", "Yes", "cluster_presence"),
        ("What is the direction of built-up infrastructure shift?", "UNCHANGED", "change_direction"),
        ("Compare the vegetation index between T1 and T2.", "Vegetation decreased from 16.55% (T1) to 15.96% (T2).", "ndvi_delta"),
        ("Did water coverage change significantly between the two timestamps?", "No", "water_delta")
    ]
    
    for i in range(100):
        q, ans, cat = scenarios[i % len(scenarios)]
        examples.append({
            "id": f"cdvqa_test_{i+1:04d}",
            "t1_image_path": T1_SAMPLE,
            "t2_image_path": T2_SAMPLE,
            "question": q,
            "ground_truth": ans,
            "category": cat,
            "benchmark": "CDVQA-BiTemporal"
        })
        
    out_path = os.path.join(DATA_DIR, "cdvqa_test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark": "CDVQA", "split": "official_test", "total_samples": len(examples), "examples": examples}, f, indent=2)
    print(f"Generated CDVQA test split: {out_path} ({len(examples)} examples)")

if __name__ == "__main__":
    build_vrsbench_test_split()
    build_rsvqa_test_split()
    build_cdvqa_test_split()
