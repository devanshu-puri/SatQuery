import React from 'react';
import { FaSatellite } from 'react-icons/fa6';
import { FiCpu, FiClock, FiActivity } from 'react-icons/fi';

const Header = ({ onOpenModels, onOpenHistory, healthStatus }) => {
    const scrollTo = (id) => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    };

    const isHealthy = healthStatus?.status === 'healthy';

    return (
        <header className="flex items-center justify-between px-6 py-3 bg-space-900/95 backdrop-blur-xl border-b border-space-700/60 text-white z-[100]">
            <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-accent-cyan/15 border border-accent-cyan/30 text-accent-cyan">
                    <FaSatellite size={20} />
                </div>
                <div>
                    <div className="flex items-center gap-2">
                        <span className="text-base font-bold tracking-tight">
                            SatQuery <span className="bg-gradient-to-r from-accent-cyan to-accent-blue bg-clip-text text-transparent">AI</span>
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-space-800 border border-space-700 text-gray-300 font-mono">
                            ISRO/SAC #26167
                        </span>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-3">
                {/* System Health Badge */}
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-space-800/80 border border-space-700 text-xs">
                    <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
                    <span className="text-gray-300 font-medium hidden sm:inline">
                        {isHealthy ? 'Systems Operational' : 'Ready (Demo/Upload)'}
                    </span>
                </div>

                {/* Model Registry Button */}
                <button
                    onClick={onOpenModels}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-space-800/80 hover:bg-space-700 border border-space-700 text-xs font-semibold text-gray-200 hover:text-accent-cyan transition-colors"
                >
                    <FiCpu className="text-accent-cyan" /> Model Registry
                </button>

                {/* Session History Button */}
                <button
                    onClick={onOpenHistory}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-space-800/80 hover:bg-space-700 border border-space-700 text-xs font-semibold text-gray-200 hover:text-accent-cyan transition-colors"
                >
                    <FiClock className="text-accent-cyan" /> History
                </button>

                <div className="hidden md:flex items-center gap-1.5 text-xs text-gray-300 px-3 py-1.5 rounded-lg border border-space-700 bg-space-900/60">
                    <span>🇮🇳</span> ISRO SAC Arena
                </div>
            </div>
        </header>
    );
};

export default Header;
