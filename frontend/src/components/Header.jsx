import React from 'react';
import { FaSatellite } from 'react-icons/fa6';
import { FiCpu, FiClock, FiActivity } from 'react-icons/fi';

const Header = ({ onOpenModels, onOpenHistory, onOpenEvaluation, healthStatus }) => {
    const isHealthy = healthStatus?.status === 'healthy';

    return (
        <header className="cohere-header">
            <div className="flex items-center gap-3">
                <div className="brand-mark"><FaSatellite size={18} /></div>
                <div className="flex items-center gap-2">
                    <span className="text-base font-semibold tracking-tight text-[#17171c]">SatQuery <span className="text-[#003c33]">AI</span></span>
                    <span className="system-label">ISRO/SAC #26167</span>
                </div>
            </div>
            <div className="flex items-center gap-2">
                <div className="health-chip">
                    <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'}`} />
                    <span className="hidden sm:inline">{isHealthy ? 'Systems operational' : 'Demo and upload ready'}</span>
                </div>
                <button onClick={onOpenEvaluation} className="header-action header-action-primary"><FiActivity /> <span className="hidden lg:inline">Benchmark</span></button>
                <button onClick={onOpenModels} className="header-action"><FiCpu /> <span className="hidden lg:inline">Models</span></button>
                <button onClick={onOpenHistory} className="header-action"><FiClock /> <span className="hidden lg:inline">History</span></button>
            </div>
        </header>
    );
};

export default Header;
