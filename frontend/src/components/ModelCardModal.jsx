import React from 'react';
import { FiX, FiCpu, FiDatabase, FiCheckCircle, FiLayers } from 'react-icons/fi';

const ModelCardModal = ({ isOpen, onClose, models }) => {
    if (!isOpen) return null;

    const modelList = Object.values(models || {});

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

                {/* Model Cards Grid */}
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
                                <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                                    <FiCheckCircle size={14} /> {m.status || 'Active & Loaded'}
                                </span>
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

                            {/* Capabilities */}
                            {m.capabilities && (
                                <div>
                                    <p className="text-[11px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">Capabilities & Tasks:</p>
                                    <div className="flex flex-wrap gap-1.5">
                                        {m.capabilities.map((cap) => (
                                            <span
                                                key={cap}
                                                className="text-[11px] px-2.5 py-1 rounded-md bg-space-900 border border-space-700 text-gray-300"
                                            >
                                                ✓ {cap}
                                            </span>
                                        ))}
                                    </div>
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
