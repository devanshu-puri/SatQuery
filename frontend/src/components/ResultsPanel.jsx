import React, { useState } from 'react';
import { FiDownload, FiCheckCircle, FiCpu, FiCode, FiChevronDown, FiChevronUp, FiShare2, FiFileText } from 'react-icons/fi';
import { FaWandMagicSparkles } from 'react-icons/fa6';
import { downloadPdfReport } from '../api';

const ResultsPanel = ({
    query,
    sentinelData,
    agentResult,
    primaryUpload,
    secondaryUpload,
    selectedDemoSample,
    isStreaming,
    streamSteps
}) => {
    const [traceOpen, setTraceOpen] = useState(true);
    const [downloadingPdf, setDownloadingPdf] = useState(false);

    if (isStreaming) {
        return (
            <div className="w-1/4 h-full flex flex-col bg-space-900/95 backdrop-blur-xl text-white border-l border-space-700/60 p-5 overflow-y-auto">
                <div className="flex items-center gap-2 mb-4 text-xs font-bold text-accent-cyan">
                    <div className="w-4 h-4 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin"></div>
                    <span>Agent Orchestrating Pipeline...</span>
                </div>
                <div className="space-y-2 font-mono text-xs text-gray-300 bg-space-950/80 p-3 rounded-xl border border-space-800">
                    {streamSteps.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-2 animate-fadeIn">
                            <span className="text-accent-cyan">✓</span>
                            <div>
                                <p className="font-semibold text-white">{step.step}</p>
                                <p className="text-[10px] text-gray-400">{step.detail}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (!agentResult) {
        return (
            <div className="w-1/4 h-full flex flex-col items-center justify-center text-center bg-space-900/95 backdrop-blur-xl text-gray-400 border-l border-space-700/60 p-6">
                <FaWandMagicSparkles size={32} className="mb-3 text-accent-cyan/60 animate-bounce" />
                <h3 className="font-semibold text-white text-sm mb-1">ISRO Multi-Modal AI Ready</h3>
                <p className="text-xs leading-relaxed text-gray-400">
                    Select a Demo Benchmark pair or upload a GeoTIFF raster, select a specialist tool task, and run analysis to inspect multi-modal reasoning and auditable execution traces.
                </p>
            </div>
        );
    }

    const trace = agentResult.execution_trace || {};
    const confidencePct = Math.round((agentResult.confidence_score || 0.90) * 100);

    const handleDownloadPdf = async () => {
        setDownloadingPdf(true);
        try {
            const preview = agentResult.preview_url || primaryUpload?.metadata?.preview_url || selectedDemoSample?.preview_url || sentinelData?.thumb_url;
            const blob = await downloadPdfReport(agentResult, preview);
            const url = window.URL.createObjectURL(new Blob([blob], { type: 'application/pdf' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `satquery-isro-evaluation-${Date.now()}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (e) {
            console.error(e);
            alert('Failed to generate PDF report.');
        } finally {
            setDownloadingPdf(false);
        }
    };

    const handleExportGeoJSON = () => {
        if (!agentResult.visual_evidence) {
            alert('No vector GeoJSON features in this result to export.');
            return;
        }
        const blob = new Blob([JSON.stringify(agentResult.visual_evidence, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `satquery-grounding-vector-${Date.now()}.geojson`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
    };

    return (
        <div className="w-1/4 h-full flex flex-col bg-space-900/95 backdrop-blur-xl text-white border-l border-space-700/60 p-4 overflow-y-auto">
            {/* Header & Confidence Badge */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-1.5 text-xs font-bold text-gray-200">
                    <FaWandMagicSparkles className="text-accent-cyan" /> Multi-Modal AI Results
                </div>
                <div className="flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-accent-cyan/15 border border-accent-cyan/40 text-accent-cyan text-xs font-bold">
                    <FiCheckCircle className="text-xs" /> {confidencePct}% Conf.
                </div>
            </div>

            {/* Task & Model Info */}
            <div className="p-2.5 rounded-xl bg-space-950/80 border border-space-800 mb-3 space-y-1 text-xs">
                <div className="flex justify-between items-center">
                    <span className="text-gray-400">Task Mode:</span>
                    <span className="font-semibold text-accent-cyan uppercase tracking-wider text-[11px]">
                        {agentResult.task_type?.replace(/_/g, ' ')}
                    </span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-gray-400">Model Invoked:</span>
                    <span className="font-medium text-gray-200">{trace.model_invoked || 'GeoChat-7B'}</span>
                </div>
                <div className="flex justify-between items-center gap-2">
                    <span className="text-gray-400">Tool Category:</span>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide ${trace.tool_category === 'classical_rs' ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'}`}>
                        {trace.tool_category || 'ai_specialist_model'}
                    </span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-gray-400">Adapter:</span>
                    <span className="font-mono text-[10px] text-accent-cyan">{trace.adapter_used || 'adapter_a'}</span>
                </div>
                <div className="flex justify-between items-center">
                    <span className="text-gray-400">Latency:</span>
                    <span className="font-mono text-gray-300">{trace.latency_ms || 320} ms</span>
                </div>
            </div>

            {/* AI Textual Analysis */}
            <div className="mb-3">
                <label className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
                    Multi-Modal RS-VLM Insights
                </label>
                <div className="p-2.5 rounded-xl bg-space-950/70 border border-space-800 text-xs text-gray-200 leading-relaxed">
                    {agentResult.response}
                </div>
            </div>

            {/* Extra Task Statistics if present */}
            {agentResult.extra_stats && Object.keys(agentResult.extra_stats).length > 0 && (
                <div className="grid grid-cols-2 gap-2 mb-3">
                    {agentResult.extra_stats.change_percentage !== undefined && (
                        <div className="p-2 rounded-lg bg-space-950 border border-space-800 text-center">
                            <p className="text-[10px] text-gray-400">Surface Change</p>
                            <p className="text-xs font-bold text-accent-cyan">{agentResult.extra_stats.change_percentage}%</p>
                        </div>
                    )}
                    {agentResult.extra_stats.detected_clusters_count !== undefined && (
                        <div className="p-2 rounded-lg bg-space-950 border border-space-800 text-center">
                            <p className="text-[10px] text-gray-400">Change Clusters</p>
                            <p className="text-xs font-bold text-white">{agentResult.extra_stats.detected_clusters_count}</p>
                        </div>
                    )}
                    {agentResult.extra_stats.sar_water_coverage_pct !== undefined && (
                        <div className="p-2 rounded-lg bg-space-950 border border-space-800 text-center">
                            <p className="text-[10px] text-gray-400">SAR Water Extent</p>
                            <p className="text-xs font-bold text-accent-cyan">{agentResult.extra_stats.sar_water_coverage_pct}%</p>
                        </div>
                    )}
                    {agentResult.extra_stats.detected_count !== undefined && (
                        <div className="p-2 rounded-lg bg-space-950 border border-space-800 text-center">
                            <p className="text-[10px] text-gray-400">Grounded Polygons</p>
                            <p className="text-xs font-bold text-accent-cyan">{agentResult.extra_stats.detected_count}</p>
                        </div>
                    )}
                </div>
            )}

            {/* Visual Evidence Preview */}
            {(agentResult.preview_url || primaryUpload?.metadata?.preview_url || selectedDemoSample?.preview_url) && (
                <div className="mb-3">
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">
                        Visual Evidence Artifact
                    </label>
                    <div className="rounded-xl overflow-hidden border border-space-800 bg-space-950 p-1">
                        <img
                            src={agentResult.preview_url || primaryUpload?.metadata?.preview_url || selectedDemoSample?.preview_url}
                            alt="Visual Evidence"
                            className="w-full aspect-video object-cover rounded-lg"
                        />
                    </div>
                </div>
            )}

            {/* Auditable Execution Trace Drawer */}
            <div className="mt-auto border-t border-space-800 pt-2.5">
                <button
                    onClick={() => setTraceOpen(o => !o)}
                    className="w-full flex items-center justify-between text-xs font-semibold text-gray-400 hover:text-white py-1 transition-colors"
                >
                    <span className="flex items-center gap-1.5 text-accent-cyan">
                        <FiCpu /> Auditable Execution Trace (Grading Log)
                    </span>
                    {traceOpen ? <FiChevronUp /> : <FiChevronDown />}
                </button>

                {traceOpen && (
                    <div className="mt-1.5 p-2 rounded-lg bg-space-950 border border-space-800 font-mono text-[10px] text-gray-300 space-y-0.5 overflow-x-auto max-h-32">
                        <p><span className="text-accent-cyan">Task:</span> {trace.task_selected}</p>
                        <p><span className="text-accent-cyan">Decision:</span> {trace.router_decision}</p>
                        <p><span className="text-accent-cyan">Tools:</span> {trace.tools_executed?.join(', ')}</p>
                        <p><span className="text-accent-cyan">CRS:</span> {trace.input_metadata?.primary_crs}</p>
                    </div>
                )}

                {/* Actions: GeoJSON Export & PDF Export */}
                <div className="grid grid-cols-2 gap-2 mt-2.5">
                    {agentResult.visual_evidence && (
                        <button
                            onClick={handleExportGeoJSON}
                            className="flex items-center justify-center gap-1 py-1.5 rounded-lg bg-space-800 hover:bg-space-700 border border-space-700 text-[11px] font-semibold text-gray-200 transition-colors"
                        >
                            <FiShare2 /> Export GeoJSON
                        </button>
                    )}
                    <button
                        onClick={handleDownloadPdf}
                        disabled={downloadingPdf}
                        className={`${
                            agentResult.visual_evidence ? 'col-span-1' : 'col-span-2'
                        } flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-gradient-to-r from-accent-cyan/20 to-accent-blue/20 border border-accent-cyan/40 hover:border-accent-cyan text-[11px] font-bold text-white transition-all shadow-md`}
                    >
                        <FiDownload /> {downloadingPdf ? 'Generating...' : 'Download ISRO PDF'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ResultsPanel;
