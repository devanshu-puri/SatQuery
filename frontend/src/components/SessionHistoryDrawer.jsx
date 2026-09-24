import React from 'react';
import { FiClock, FiX, FiCheckCircle, FiChevronRight, FiCpu } from 'react-icons/fi';

const SessionHistoryDrawer = ({ isOpen, onClose, history, onSelectHistoryItem }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-y-0 right-0 z-[2000] w-96 bg-space-900/98 backdrop-blur-xl border-l border-space-700/80 shadow-2xl p-5 text-white flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-space-700/60 mb-4">
                <div className="flex items-center gap-2 text-sm font-bold text-gray-200">
                    <FiClock className="text-accent-cyan" /> Session Query History
                </div>
                <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg hover:bg-space-800 text-gray-400 hover:text-white transition-colors"
                >
                    <FiX size={18} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {(!history || history.length === 0) ? (
                    <div className="h-full flex flex-col items-center justify-center text-center text-gray-500 p-6">
                        <FiClock size={28} className="mb-2 text-space-700" />
                        <p className="text-xs">No queries executed in this session yet.</p>
                    </div>
                ) : (
                    history.map((item, idx) => (
                        <div
                            key={item.query_id || idx}
                            onClick={() => {
                                onSelectHistoryItem(item);
                                onClose();
                            }}
                            className="p-3 rounded-xl bg-space-800/70 hover:bg-space-800 border border-space-700 hover:border-accent-cyan/60 cursor-pointer transition-all space-y-2 group"
                        >
                            <div className="flex items-center justify-between text-[11px]">
                                <span className="font-semibold text-accent-cyan uppercase tracking-wider">
                                    {item.task_type?.replace(/_/g, ' ')}
                                </span>
                                <span className="text-gray-400">
                                    {Math.round((item.confidence_score || 0.9) * 100)}% Conf.
                                </span>
                            </div>
                            <p className="text-xs text-gray-200 font-medium line-clamp-2">
                                "{item.query}"
                            </p>
                            <div className="flex items-center justify-between text-[10px] text-gray-400 border-t border-space-700/40 pt-1.5">
                                <span className="flex items-center gap-1">
                                    <FiCpu className="text-accent-cyan" /> {item.execution_trace?.model_invoked?.split(' ')[0] || 'GeoChat'}
                                </span>
                                <span className="flex items-center gap-1 group-hover:text-accent-cyan transition-colors">
                                    Restore <FiChevronRight />
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default SessionHistoryDrawer;
