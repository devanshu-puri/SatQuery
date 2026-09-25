import React, { useMemo, useState } from 'react';
import { FiX, FiCpu, FiDatabase, FiCheckCircle, FiLayers, FiShield } from 'react-icons/fi';

const ModelCardModal = ({ isOpen, onClose, models, integrity, onRefreshIntegrity }) => {
    const [activeTab, setActiveTab] = useState('integrity');

    if (!isOpen) return null;

    const modelList = Object.values(models || {});
    const integrityRows = useMemo(() => {
        const orderedKeys = ['rs_adaptation', 'vrsbench_eval', 'rsvqa_eval', 'cdvqa_eval', 'risat_data', 'geochat_checkpoint', 'change_model', 'fusion_model'];
        return orderedKeys.flatMap((key) => {
            const value = integrity?.[key] ?? (key === 'rs_adaptation' ? integrity?.bigearthnet_adapter : null);
            return value === undefined || value === null ? [] : [[key, value]];
        });
    }, [integrity]);

    const statusColors = {
        PASS: 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30',
        PARTIAL: 'bg-amber-500/10 text-amber-300 border border-amber-500/30',
        MOCKED: 'bg-red-500/10 text-red-300 border border-red-500/30',
    };

    const renderIntegrityTable = () => (
        <div className="mb-6 rounded-2xl border border-space-700/80 bg-space-950/60 p-4">
            <div className="mb-3 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                        <FiShield size={18} />
                    </div>
                    <div>
                        <h3 className="text-base font-bold text-white">System Integrity</h3>
                        <p className="text-[11px] text-gray-400">Computed live from the actual filesystem, result files, and runtime probes.</p>
                    </div>
                </div>

                <button
                    type="button"
                    onClick={onRefreshIntegrity}
                    className="inline-flex items-center gap-2 rounded-lg border border-cyan-500/40 bg-cyan-500/10 px-3 py-1.5 text-[11px] font-semibold text-cyan-200 hover:bg-cyan-500/20"
                >
                    Re-run integrity check
                </button>
            </div>

            <div className="overflow-hidden rounded-xl border border-space-700/70">
                <table className="min-w-full divide-y divide-space-700/80 text-left text-xs">
                    <thead className="bg-space-900/80 text-gray-400">
                        <tr>
                            <th className="px-3 py-2 font-semibold">Asset</th>
                            <th className="px-3 py-2 font-semibold">Status</th>
                            <th className="px-3 py-2 font-semibold">Evidence</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-space-700/60 bg-space-900/40 text-gray-200">
                        {integrityRows.length > 0 ? integrityRows.map(([key, value]) => (
                            <tr key={key}>
                                <td className="px-3 py-2 font-medium text-white">
                                    {key.replace(/_/g, ' ')}
                                </td>
                                <td className="px-3 py-2">
                                    <span className={`inline-flex rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide ${statusColors[value?.status] || 'bg-gray-500/10 text-gray-300 border border-gray-500/30'}`}>
                                        {value?.status || 'UNKNOWN'}
                                    </span>
                                </td>
                                <td className="px-3 py-2 text-gray-300">
                                    {value?.manifest ? `Manifest loaded: ${Object.keys(value.manifest).slice(0, 2).join(', ')}` : value?.result ? `Result file loaded (${Object.keys(value.result).slice(0, 2).join(', ')})` : value?.note || value?.message || 'No runtime artifact found'}
                                </td>
                            </tr>
                        )) : (
                            <tr>
                                <td className="px-3 py-3 text-gray-400" colSpan="3">Integrity data is still loading…</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );

    return (
        <div className="fixed inset-0 z-[2000] flex items-center justify-center bg-black/75 backdrop-blur-md p-4">
            <div className="relative w-full max-w-4xl max-h-[85vh] overflow-y-auto rounded-2xl bg-space-900 border border-space-700/80 shadow-2xl p-6 text-white">
                {/* Header */}
                <div className="flex items-center justify-between pb-4 border-b border-space-700/60 mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-accent-cyan/15 border border-accent-cyan/30 text-accent-cyan">
                            <FiCpu size={22} />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                Remote Sensing Model Registry & Fine-Tuning Provenance
                            </h2>
                            <p className="text-xs text-gray-400">
                                Certified RS-Adapted Multi-Modal Vision-Language Architecture (ISRO / SAC PS #26167)
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-space-800 text-gray-400 hover:text-white transition-colors"
                    >
                        <FiX size={20} />
                    </button>
                </div>

                <div className="mb-5 flex items-center gap-2 rounded-xl border border-space-700/80 bg-space-950/50 p-1">
                    {[
                        { id: 'integrity', label: 'System Integrity', icon: FiShield },
                        { id: 'registry', label: 'Model Registry', icon: FiCpu },
                    ].map(({ id, label, icon: Icon }) => (
                        <button
                            key={id}
                            type="button"
                            onClick={() => setActiveTab(id)}
                            className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold transition-all ${
                                activeTab === id
                                    ? 'bg-cyan-500/15 text-cyan-200 border border-cyan-500/30'
                                    : 'text-gray-300 hover:bg-space-800'
                            }`}
                        >
                            <Icon size={14} />
                            {label}
                        </button>
                    ))}
                </div>

                {activeTab === 'integrity' ? renderIntegrityTable() : (
                    <div className="space-y-4">
                        {modelList.map((m) => (
                            <div
                                key={m.id || m.name}
                                className="p-4 rounded-xl bg-space-800/80 border border-space-700/70 hover:border-accent-cyan/50 transition-all space-y-3"
                            >
                                <div className="flex items-start justify-between">
                                    <div>
                                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-accent-cyan/15 text-accent-cyan font-bold uppercase tracking-wider">
                                            {m.id}
                                        </span>
                                        <h3 className="text-base font-bold text-white mt-1">{m.name}</h3>
                                        <p className="text-xs text-gray-400">{m.domain}</p>
                                    </div>
                                    <div className="flex flex-col items-end gap-2">
                                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-[9px] font-bold uppercase tracking-wide ${m.tool_category === 'classical_rs' ? 'bg-amber-500/10 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/30'}`}>
                                            {m.tool_category || 'ai_specialist_model'}
                                        </span>
                                        <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                                            <FiCheckCircle size={14} /> {m.status || 'Active & Loaded'}
                                        </span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs bg-space-950/60 p-3 rounded-lg border border-space-800">
                                    <div>
                                        <p className="text-gray-500 flex items-center gap-1 font-semibold mb-0.5">
                                            <FiLayers className="text-accent-cyan" /> Architecture & Backbone:
                                        </p>
                                        <p className="text-gray-200">{m.architecture || m.name}</p>
                                    </div>
                                    <div>
                                        <p className="text-gray-500 flex items-center gap-1 font-semibold mb-0.5">
                                            <FiDatabase className="text-accent-cyan" /> Fine-Tuning Provenance:
                                        </p>
                                        <p className="text-accent-cyan font-medium">{m.fine_tuning_provenance || m.fine_tuning_base}</p>
                                    </div>
                                </div>

                                {(m.official_scope || m.scope_claim || m.additional_features || m.capabilities) && (
                                    <div>
                                        {m.scope_claim && (
                                            <p className="text-[11px] font-semibold text-accent-cyan mb-1.5 uppercase tracking-wider">Official Mandatory Scope</p>
                                        )}
                                        {m.scope_claim && (
                                            <p className="text-[11px] text-gray-300 mb-2">{m.scope_claim}</p>
                                        )}
                                        {m.official_scope && (
                                            <div className="flex flex-wrap gap-1.5 mb-2">
                                                {m.official_scope.map((cap) => (
                                                    <span key={cap} className="text-[11px] px-2.5 py-1 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-200">
                                                        ✓ {cap}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        {m.additional_features && m.additional_features.length > 0 && (
                                            <div className="mb-2">
                                                <p className="text-[11px] font-semibold text-gray-400 mb-1 uppercase tracking-wider">Additional Feature</p>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {m.additional_features.map((feature) => (
                                                        <span key={feature} className="text-[11px] px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-200">
                                                            • {feature}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        {m.capabilities && (
                                            <div>
                                                <p className="text-[11px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">Capabilities & Tasks:</p>
                                                <div className="flex flex-wrap gap-1.5">
                                                    {m.capabilities.map((cap) => (
                                                        <span key={cap} className="text-[11px] px-2.5 py-1 rounded-md bg-space-900 border border-space-700 text-gray-300">
                                                            ✓ {cap}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {(m.adapter_sha256 || m.training_manifest || m.training_loss_file || m.training_loss_plot) && (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 border-t border-space-700/40 pt-2 text-[11px] text-gray-300">
                                        {m.adapter_sha256 && (
                                            <div>
                                                <p className="text-gray-500 font-semibold uppercase tracking-wider mb-1">Adapter SHA-256</p>
                                                <p className="font-mono text-accent-cyan break-all">{m.adapter_sha256}</p>
                                            </div>
                                        )}
                                        {m.training_loss_file && (
                                            <div>
                                                <p className="text-gray-500 font-semibold uppercase tracking-wider mb-1">Loss Curve</p>
                                                <p className="text-gray-200">{m.training_loss_file}</p>
                                            </div>
                                        )}
                                        {m.training_manifest && (
                                            <div className="md:col-span-2">
                                                <p className="text-gray-500 font-semibold uppercase tracking-wider mb-1">Training Manifest</p>
                                                <p className="text-gray-200">Dataset: {m.training_manifest.dataset || 'N/A'} • Epochs: {m.training_manifest.num_epochs || 'N/A'} • Final Loss: {m.training_manifest.final_loss ?? 'N/A'}</p>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {m.parameters && (
                                    <p className="text-[11px] font-mono text-gray-400 border-t border-space-700/40 pt-2">
                                        <span className="text-gray-500">Parameters / Adapter Weights:</span> {m.parameters}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                <div className="mt-6 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-5 py-2 rounded-lg bg-space-800 hover:bg-space-700 text-xs font-semibold text-white transition-colors"
                    >
                        Close Registry
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ModelCardModal;
