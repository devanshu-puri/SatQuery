import urllib.request
import json

queries = [
    ("1. VQA Overview", "What is in this image?", "Text"),
    ("2. Binary Water Check", "Is there water?", "Text"),
    ("3. Water Grounding", "Where is the water?", "Bounding box"),
    ("4. Segmentation & Mask", "Show exact water region", "Mask"),
    ("5. Change Detection", "What changed?", "Change map + text"),
    ("6. Forest Measurement", "How much forest is there?", "Mask + Area"),
    ("7. Land Classification", "What type of land is this?", "Class"),
    ("8. Optical + SAR Fusion", "Use optical + SAR", "Combined analysis"),
    ("9. Geospatial Coordinates", "Give coordinates", "Coordinates"),
    ("10. Explainable Built-Up Evidence", "Explain why this is built-up", "Explanation + evidence")
]

print("=" * 70)
print("TESTING ALL 10 INTENTS & MAIN OUTPUTS")
print("=" * 70)

for title, q, expected_output in queries:
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/query",
        data=json.dumps({"query": q}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"[{title}]")
            print(f"  Query: \"{q}\"")
            print(f"  Target Output: {expected_output}")
            print(f"  Task Mode: {data.get('task_type')}")
            print(f"  Confidence: {int(data.get('confidence_score', 0)*100)}%")
            print(f"  Response Snippet:\n    {data.get('response')[:120]}...")
            if data.get("visual_evidence"):
                print(f"  Visual Evidence: GeoJSON FeatureCollection ({len(data['visual_evidence']['features'])} features)")
            if data.get("preview_url"):
                print("  Visual Overlay Artifact: Present")
            print("-" * 70)
    except Exception as e:
        print(f"FAIL on {title}: {e}")
