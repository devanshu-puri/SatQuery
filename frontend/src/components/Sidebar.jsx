import React, { useState } from 'react';
import { FiChevronDown, FiMapPin, FiUploadCloud, FiLayers, FiCheckCircle, FiPlay, FiCpu } from 'react-icons/fi';
import { uploadRasterFile } from '../api';

const TASK_PRESETS = [
    {
        id: 'single_image_vqa',
        icon: '📸',
        label: 'Single-Image RS-VQA',
        desc: 'Visual Question Answering on optical/multispectral scene',
        sampleQuery: 'What is the agricultural and crop condition in this scene?'
    },
    {
        id: 'region_grounding',
        icon: '🎯',
        label: 'Region Grounding & Caption',
        desc: 'Locate objects with vector GeoJSON bounding polygons',
        sampleQuery: 'Locate all dense vegetation areas and built structures'
    },
    {
        id: 'bitemporal_change',
        icon: '⏳',
        label: 'Bi-Temporal Change ($T_1, T_2$)',
        desc: 'Compare dual timestamps for difference mapping & Change-VQA',
        sampleQuery: 'Compare before and after satellite images to detect significant land-cover change'
    },
    {
        id: 'optical_sar_fusion',
        icon: '🛰️',
        label: 'Optical + SAR Radar Fusion',
        desc: 'Jointly process Optical + C-band SAR (VV/VH) backscatter',
        sampleQuery: 'Perform optical and SAR radar cross-modal fusion for all-weather water mapping'
    }
];

const selectClasses = "w-full appearance-none p-2.5 pr-9 bg-space-900/60 rounded-lg border border-space-700 text-xs text-white outline-none transition-colors focus:border-accent-cyan focus:ring-1 focus:ring-accent-cyan/50 disabled:opacity-40 disabled:cursor-not-allowed";

const Sidebar = ({
    states,
    selectedState,
    onStateChange,
    areas,
    selectedArea,
    onAreaChange,
    onExploreArea,
    query,
    onQueryChange,
    onAnalyze,
    canAnalyze,
    activeMode,
    onModeChange,
    primaryUpload,
    onPrimaryUpload,
    secondaryUpload,
    onSecondaryUpload,
    selectedTaskId,
    onSelectTaskId,
    demoSamples,
    selectedDemoSample,
    onSelectDemoSample,
    geeStartDate,
    onGeeStartDateChange,
    geeEndDate,
    onGeeEndDateChange,
    geeCloudCover,
    onGeeCloudCoverChange
}) => {
    const [uploadingPrimary, setUploadingPrimary] = useState(false);
    const [uploadingSecondary, setUploadingSecondary] = useState(false);

    const handlePrimaryFile = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setUploadingPrimary(true);
        try {
            const data = await uploadRasterFile(file);
            onPrimaryUpload(data);
        } catch (err) {
            console.error(err);
            alert('Failed to parse uploaded raster file.');
        } finally {
            setUploadingPrimary(false);
        }
    };

    const handleSecondaryFile = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setUploadingSecondary(true);
        try {
            const data = await uploadRasterFile(file);
            onSecondaryUpload(data);
        } catch (err) {
            console.error(err);
            alert('Failed to parse secondary raster file.');
        } finally {
            setUploadingSecondary(false);
        }
    };

    return (
        <div className="w-1/4 h-full flex flex-col bg-space-900/95 backdrop-blur-xl text-white shadow-2xl border-r border-space-700/60 p-4 overflow-y-auto">
            {/* 3-Way Mode Switcher */}
            <div className="flex rounded-xl bg-space-950 p-1 border border-space-800 mb-3 text-[11px] font-semibold">
                <button
                    onClick={() => onModeChange('demo')}
                    className={`flex-1 py-1.5 rounded-lg transition-all ${
                        activeMode === 'demo' ? 'bg-accent-cyan text-space-900 shadow-md font-bold' : 'text-gray-400 hover:text-white'
                    }`}
                >
                    🚀 Demo Pairs
                </button>
                <button
                    onClick={() => onModeChange('upload')}
                    className={`flex-1 py-1.5 rounded-lg transition-all ${
                        activeMode === 'upload' ? 'bg-accent-cyan text-space-900 shadow-md font-bold' : 'text-gray-400 hover:text-white'
                    }`}
                >
                    📁 Upload GeoTIFF
                </button>
                <button
                    onClick={() => onModeChange('gee')}
                    className={`flex-1 py-1.5 rounded-lg transition-all ${
                        activeMode === 'gee' ? 'bg-accent-cyan text-space-900 shadow-md font-bold' : 'text-gray-400 hover:text-white'
                    }`}
                >
                    🛰️ GEE Live
                </button>
            </div>

            {/* Mode 1: Demo Benchmarks */}
            {activeMode === 'demo' && (
                <div className="space-y-2.5 mb-3 bg-space-950/60 p-2.5 rounded-xl border border-space-800">
                    <div className="flex items-center justify-between text-[11px] font-semibold text-gray-300">
                        <span className="flex items-center gap-1.5 text-accent-cyan">
                            <FiPlay /> Preloaded Benchmark Datasets
                        </span>
                    </div>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-0.5">
                        {demoSamples?.map((s) => (
                            <button
                                key={s.id}
                                onClick={() => onSelectDemoSample(s)}
                                className={`w-full text-left p-2 rounded-lg border text-xs transition-all ${
                                    selectedDemoSample?.id === s.id
                                        ? 'bg-accent-cyan/15 border-accent-cyan text-accent-cyan font-semibold'
                                        : 'bg-space-900/60 border-space-700/60 text-gray-300 hover:bg-space-800'
                                }`}
                            >
                                <p className="font-semibold text-[11px] leading-tight text-white">{s.title}</p>
                                <p className="text-[10px] text-gray-400 mt-0.5 truncate">{s.provenance}</p>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Mode 2: GeoTIFF Upload */}
            {activeMode === 'upload' && (
                <div className="space-y-2 mb-3 bg-space-950/60 p-2.5 rounded-xl border border-space-800">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-300">
                        <FiUploadCloud className="text-accent-cyan" /> GeoTIFF / Multi-Modal Ingestion
                    </div>

                    <div className="p-2 rounded-lg border border-dashed border-space-700 bg-space-900/40">
                        <label className="block text-[11px] font-medium text-gray-300 mb-1">
                            Primary Raster (Optical / $T_1$ / GeoTIFF)
                        </label>
                        <input
                            type="file"
                            accept=".tif,.tiff,.geotiff,.png,.jpg"
                            onChange={handlePrimaryFile}
                            className="text-[10px] text-gray-400 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[10px] file:font-semibold file:bg-space-700 file:text-accent-cyan hover:file:bg-space-600"
                        />
                        {uploadingPrimary && <p className="text-[10px] text-accent-cyan mt-1 animate-pulse">Profiling raster...</p>}
                        {primaryUpload?.metadata && (
                            <div className="mt-1.5 text-[10px] text-gray-400 space-y-0.5 bg-space-900 p-1.5 rounded">
                                <p className="text-accent-cyan font-semibold truncate">{primaryUpload.metadata.filename}</p>
                                <p>CRS: <span className="text-white">{primaryUpload.metadata.crs}</span> | Modality: <span className="text-white">{primaryUpload.metadata.modality}</span></p>
                            </div>
                        )}
                    </div>

                    <div className="p-2 rounded-lg border border-dashed border-space-700 bg-space-900/40">
                        <label className="block text-[11px] font-medium text-gray-300 mb-1">
                            Secondary Raster ($T_2$ or SAR) (Optional)
                        </label>
                        <input
                            type="file"
                            accept=".tif,.tiff,.geotiff,.png,.jpg"
                            onChange={handleSecondaryFile}
                            className="text-[10px] text-gray-400 file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-[10px] file:font-semibold file:bg-space-700 file:text-accent-cyan hover:file:bg-space-600"
                        />
                        {uploadingSecondary && <p className="text-[10px] text-accent-cyan mt-1 animate-pulse">Profiling secondary...</p>}
                        {secondaryUpload?.metadata && (
                            <div className="mt-1.5 text-[10px] text-gray-400 space-y-0.5 bg-space-900 p-1.5 rounded">
                                <p className="text-accent-cyan font-semibold truncate">{secondaryUpload.metadata.filename}</p>
                                <p>Modality: <span className="text-white">{secondaryUpload.metadata.modality}</span></p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Mode 3: GEE Live AOI */}
            {activeMode === 'gee' && (
                <div className="space-y-2 mb-3 bg-space-950/60 p-2.5 rounded-xl border border-space-800">
                    <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-300">
                        <FiMapPin className="text-accent-cyan" /> GEE Live AOI & Server-Side Filtering
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        <div>
                            <label className="block text-[10px] uppercase text-gray-500 mb-0.5">State</label>
                            <div className="relative">
                                <select value={selectedState} onChange={onStateChange} className={selectClasses}>
                                    <option value="">Select</option>
                                    {states.map(s => <option key={s} value={s}>{s}</option>)}
                                </select>
                                <FiChevronDown className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-500" />
                            </div>
                        </div>
                        <div>
                            <label className="block text-[10px] uppercase text-gray-500 mb-0.5">District</label>
                            <div className="relative">
                                <select value={selectedArea} onChange={onAreaChange} disabled={!selectedState} className={selectClasses}>
                                    <option value="">Select</option>
                                    {areas.map(a => <option key={a} value={a}>{a}</option>)}
                                </select>
                                <FiChevronDown className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-gray-500" />
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                            <label className="block text-[10px] text-gray-400 mb-0.5">Start Date</label>
                            <input
                                type="date"
                                value={geeStartDate}
                                onChange={(e) => onGeeStartDateChange(e.target.value)}
                                className="w-full p-1.5 bg-space-900 rounded border border-space-700 text-[11px] text-white outline-none"
                            />
                        </div>
                        <div>
                            <label className="block text-[10px] text-gray-400 mb-0.5">End Date</label>
                            <input
                                type="date"
                                value={geeEndDate}
                                onChange={(e) => onGeeEndDateChange(e.target.value)}
                                className="w-full p-1.5 bg-space-900 rounded border border-space-700 text-[11px] text-white outline-none"
                            />
                        </div>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-gray-300">
                        <span>Max Cloud Cover:</span>
                        <span className="text-accent-cyan font-bold">{geeCloudCover}%</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="50"
                        value={geeCloudCover}
                        onChange={(e) => onGeeCloudCoverChange(Number(e.target.value))}
                        className="w-full accent-accent-cyan h-1"
                    />

                    <button
                        onClick={onExploreArea}
                        disabled={!selectedState || !selectedArea}
                        className="w-full py-1.5 rounded-lg bg-accent-blue hover:bg-blue-600 disabled:bg-space-700 disabled:text-gray-500 text-xs font-semibold transition-colors"
                    >
                        Fly Map to Selected District
                    </button>
                </div>
            )}

            {/* Task Selector & Query Presets */}
            <div className="border-t border-space-800 pt-2.5">
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1.5">
                    Select Specialist Tool Task
                </label>
                <div className="space-y-1 mb-2.5">
                    {TASK_PRESETS.map(task => (
                        <button
                            key={task.id}
                            onClick={() => {
                                onSelectTaskId(task.id);
                                onQueryChange(task.sampleQuery);
                            }}
                            className={`w-full flex items-center gap-2 text-left p-1.5 rounded-lg border text-xs transition-all ${
                                selectedTaskId === task.id
                                    ? 'bg-accent-cyan/15 border-accent-cyan text-accent-cyan font-medium'
                                    : 'border-space-800 bg-space-950/40 text-gray-300 hover:bg-space-800'
                            }`}
                        >
                            <span className="text-xs shrink-0">{task.icon}</span>
                            <div className="flex-1 min-w-0">
                                <p className="font-semibold text-[11px] leading-tight">{task.label}</p>
                            </div>
                        </button>
                    ))}
                </div>

                {/* Natural Language Prompt Box */}
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
                    Natural Language Query Prompt
                </label>
                <textarea
                    value={query}
                    onChange={(e) => onQueryChange(e.target.value)}
                    rows={2}
                    placeholder="Enter your remote sensing query..."
                    className="w-full p-2 bg-space-950 rounded-lg border border-space-700 text-xs text-white placeholder-gray-500 outline-none focus:border-accent-cyan resize-none"
                />

                <button
                    onClick={onAnalyze}
                    disabled={!canAnalyze}
                    className={`w-full mt-2.5 py-2 rounded-lg font-bold text-xs transition-all ${
                        canAnalyze
                            ? 'bg-gradient-to-r from-accent-blue to-accent-cyan text-space-900 hover:opacity-90 shadow-lg shadow-accent-cyan/20'
                            : 'bg-space-800 text-gray-500 cursor-not-allowed'
                    }`}
                >
                    ⚡ Run Multi-Modal Agent Analysis
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
