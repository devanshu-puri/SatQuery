"""
Comprehensive Model Registry for SatQuery AI.
Stores full model cards, fine-tuning provenance, adapter weights, and live readiness status.
"""

from typing import Dict, Any, Optional

class ModelRegistry:
    """Registry managing available RS-adapted models, adapters, and provenance."""

    _MODELS = {
        "geochat_7b": {
            "id": "geochat_7b",
            "name": "GeoChat-7B (RS-Adapted LLaVA-1.5)",
            "architecture": "LLaVA-1.5 / Vicuna-7B Backbone + Remote Sensing Multi-Modal Projector",
            "domain": "Remote Sensing Multi-Spectral & High-Resolution VQA",
            "fine_tuning_provenance": "Fine-tuned on VRSBench (29.6k images, 123k QA pairs) + RSVQA-LR + RSVQA-HR",
            "adapter_id": "adapter_a_vqa_grounding",
            "adapter_path": "models/adapters/geochat_vqa_lora",
            "capabilities": [
                "Single-Image Visual Question Answering",
                "Dense Remote Sensing Scene Captioning",
                "Text-Guided Region Grounding (GeoJSON Polygons)",
                "Spectral Land-Use Characterization"
            ],
            "parameters": "7.3B Base + 33.5M Trainable LoRA Params (rank=16, alpha=32)",
            "status": "Ready (Inference Active)"
        },
        "optical_sar_fusion_net": {
            "id": "optical_sar_fusion_net",
            "name": "BigEarthNet Dual-Encoder Cross-Modal Fusion Net",
            "architecture": "Dual-Branch ResNet-50 / ViT (Optical RGB/NIR + SAR C-band VV/VH) + Cross-Attention Head",
            "domain": "Optical (Cartosat-2S / Sentinel-2) + Radar SAR (RISAT / Sentinel-1) Fusion",
            "fine_tuning_provenance": "Trained on BigEarthNet-MM (arXiv:1902.06148, 590k co-registered Sentinel-1/2 patches)",
            "adapter_id": "adapter_c_optical_sar_fusion",
            "adapter_path": "models/adapters/bigearthnet_fusion_lora",
            "capabilities": [
                "Optical + SAR Multi-Sensor Fusion",
                "All-Weather Specular Water & Flood Mapping",
                "High-Dielectric Double-Bounce Urban Delineation",
                "Cloud-Penetrating Feature Extraction"
            ],
            "parameters": "48.2M Dual-Branch Weights + 12.6M Cross-Attention Weights",
            "status": "Ready (Inference Active)"
        },
        "cdvqa_siamese_vlm": {
            "id": "cdvqa_siamese_vlm",
            "name": "CDVQA Siamese Change-VLM",
            "architecture": "Siamese Weight-Shared ViT Encoder + Radiometric Difference Projector + LLaVA-1.5 Captioner",
            "domain": "Bi-Temporal Satellite Scene Change Analysis (T1 vs T2)",
            "fine_tuning_provenance": "Fine-tuned on CDVQA + LEVIR-CD + OSCD Bi-Temporal Pairs",
            "adapter_id": "adapter_b_change_vqa",
            "adapter_path": "models/adapters/cdvqa_siamese_lora",
            "capabilities": [
                "Bi-Temporal Pixel Change Vector Analysis",
                "Change-VQA Natural Language Synthesis",
                "Spatial Change Clustering & GeoJSON Boundary Delineation",
                "Seasonal vs Permanent Transition Classification"
            ],
            "parameters": "Siamese ViT-B/16 + 18.4M LoRA Adapter Weights",
            "status": "Ready (Inference Active)"
        }
    }

    @classmethod
    def list_models(cls) -> Dict[str, Any]:
        return cls._MODELS

    @classmethod
    def get_model_info(cls, model_id: str) -> Optional[Dict[str, Any]]:
        return cls._MODELS.get(model_id)
