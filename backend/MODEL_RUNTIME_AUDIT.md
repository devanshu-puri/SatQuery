# Model Runtime Audit

## Current architecture

`main.py` resolves the requested upload or benchmark raster, applies the current AOI crop, and passes that array through `SingleImageVQATool`. The tool uses `geospatial/model_preprocessor.py` to create the model RGB evidence artifact and `models/model_manager.py` to load a configured multimodal checkpoint.

## Model and checkpoint

- Default model ID: `MBZUAI/geochat-7B`
- Checkpoint source: `SATQUERY_VLM_CHECKPOINT`
- Adapter source: `SATQUERY_VLM_ADAPTER`
- Present in this checkout: no configured GeoChat-compatible checkpoint
- Production VQA state without that checkpoint: `NOT_AVAILABLE`; it must not be reported as a successful VLM inference.

## Adapter

`models/adapters/bigearthnet_lora/adapter_model.bin` and its manifest are present. They have not been injected into a compatible loaded base model in this environment, so their runtime state is `NOT_AVAILABLE`. Their hash and manifest are provenance, not inference proof.

## Actual inference behavior

When a compatible local checkpoint is configured, `ModelManager` performs `AutoProcessor` preprocessing and `AutoModelForVision2Seq.generate` on the current AOI artifact. It records model input dimensions, input hash, generation latency, device, dtype, and adapter state.

Without a checkpoint, single-image VQA returns an explicitly labeled classical verification fallback. `TinyRSVisionEncoder` remains in the repository only as a legacy diagnostic baseline and is not used by the production VQA tool.

## Deterministic tools

NDVI, NDWI, vegetation, flood, change-detection, optical/SAR fusion, pixel statistics, and GeoJSON conversion remain classical remote-sensing support tools. They are never VLM output.

## Benchmark execution

The existing benchmark harness lives in `benchmarks/run_all_evals.py`. Its historic result JSON files are receipts only; they do not establish that the current configured checkpoint was evaluated.

## Required production setup

1. Obtain a GeoChat-compatible local checkpoint and its official runtime implementation.
2. Set `SATQUERY_VLM_CHECKPOINT` to that directory and optionally `SATQUERY_VLM_ADAPTER` to a verified compatible adapter.
3. Run `python scripts/setup_vlm.py`.
4. Run the real-VQA tests and retain the generated runtime report.
