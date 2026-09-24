# 🛰️ SatQuery AI — Multi-Modal Remote Sensing AI Assistant
**ISRO / SAC Hackathon (Problem Statement #26167)**
*An Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries*

---

## 🌟 Overview
**SatQuery AI** is an advanced, full-stack geospatial intelligence copilot built for analyzing multi-modal remote sensing imagery using domain-adapted Vision-Language Models (VLMs), an agentic controller, and interactive Web-GIS mapping.

It provides end-to-end support for single-scene VQA, spatial region grounding (with EPSG:4326 GeoJSON vector polygons), bi-temporal change detection ($T_1, T_2$), optical-SAR radar fusion, and automated PDF evaluation summary generation with auditable execution traces.

---

## 🚀 Key Features

### 1. 🎯 4 Specialist Remote Sensing Tool Suites
- **Single-Image RS-VQA Tool**: Multi-spectral visual question answering powered by **GeoChat-7B** (adapted on VRSBench and RSVQA).
- **Text-Guided Region Grounding & Captioning**: Locates query objects in natural language and converts pixel bounding boxes to real-world **EPSG:4326 GeoJSON vector polygons**.
- **Bi-Temporal Change Detection & Change-VQA Tool ($T_1, T_2$)**: Jointly processes multi-temporal satellite pairs (CDVQA / LEVIR-CD Siamese network) and outputs difference heatmaps, change coverage $\%$, and Change-VQA insights.
- **Optical–SAR Cross-Modal Fusion Tool**: Fuses co-registered Optical (Sentinel-2 / Cartosat) + C-band Radar SAR (Sentinel-1 / RISAT VV/VH) dual-pol microwave data (BigEarthNet-MM architecture) for all-weather flood/water and urban infrastructure classification.

### 2. 🧠 Real Agentic Controller & Deterministic Router
- Dynamically inspects incoming natural language query semantics AND input raster metadata (modality, band counts, CRS, temporal pairs).
- Binds to the **Model Registry** and dispatches execution to the corresponding specialist tool.
- Emits an **Auditable Execution Trace** logging task selected, router decision rationale, model/adapter invoked, input CRS, confidence score, and latency.

### 3. 🌐 3 Ingestion Channels
- **🚀 1-Click Demo Benchmark Pairs**: Instant offline demonstration with preloaded samples from **VRSBench**, **BigEarthNet-MM**, **CDVQA**, and **ISRO Cartosat-2S / RISAT**.
- **📁 Local Multi-Modal GeoTIFF Ingestion (`POST /api/upload`)**: Full parsing with `rasterio` & `pyproj` preserving CRS, spatial extent, affine matrices, and multi-band layouts.
- **🛰️ Google Earth Engine Live AOI (`POST /api/fetch/gee`)**: Server-side filtering by drawn AOI polygon, date range, and maximum cloud-cover percentage.

### 4. 📄 Multi-Format Export
- **Download Official ISRO Evaluation PDF**: Automated ReportLab PDF generator containing metadata, AI insights, confidence scores, visual evidence crops, and execution trace tables.
- **Export GeoJSON**: Downloads vector bounding polygons for QGIS, ArcGIS, or Web-GIS applications.

---

## 🛠️ Architecture & Tech Stack

```
[ Frontend: React 19 + Vite + Tailwind CSS + Leaflet / React-Leaflet ]
                               │
                       REST & WebSockets
                               │
[ Backend: FastAPI (Python 3.14) + Uvicorn ]
   ├── Ingestion Pipeline (rasterio, GDAL, pyproj, Shapely, GEE API)
   ├── Agentic Controller & Deterministic Tool Router
   ├── Model Registry (GeoChat-7B, BigEarthNet-MM Fusion Net, CDVQA Siamese-VLM)
   ├── Specialist Tool Suites (VQA, Grounding, Change-Detection, Optical-SAR)
   └── Automated PDF Reporting (ReportLab)
```

---

## ⚡ Quick Start Guide

### Prerequisites
- **Python 3.9+** (Tested on Python 3.14)
- **Node.js 18+**

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 📚 Datasets Referenced & Benchmarked
- **BigEarthNet-MM** (*arXiv:1902.06148*): 590k co-registered Sentinel-1 SAR + Sentinel-2 Optical patches.
- **VRSBench** (*arXiv:2311.13788*): Remote sensing captioning, visual grounding, and VQA benchmark.
- **RSVQA (LR & HR)**: Low and high-resolution remote sensing question-answering benchmark.
- **CDVQA / LEVIR-CD**: Bi-temporal satellite change detection and Change-VQA benchmark.
- **ESA WorldCover v200**: 10m global land cover baseline classification.

---

## 📄 License
MIT License. Developed for the ISRO / SAC Hackathon 2026.
