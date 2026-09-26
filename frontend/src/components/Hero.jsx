import React from 'react';
import { FaLeaf, FaDroplet, FaCloudRain } from 'react-icons/fa6';
import { FiArrowDownRight } from 'react-icons/fi';
import DotGlobe from './DotGlobe';

const FEATURES = [
    { icon: FaLeaf, label: 'Vegetation', desc: 'NDVI and land-cover signals', query: 'Where is the vegetation?' },
    { icon: FaDroplet, label: 'Water', desc: 'Surface-water intelligence', query: 'Where are the water bodies?' },
    { icon: FaCloudRain, label: 'Change', desc: 'Temporal change detection', query: 'Which regions are potentially flooded?' },
];

const Hero = ({ onStartExploring, onSelectFeature }) => (
    <section id="hero" className="hero-shell">
        <div className="hero-grid">
            <div className="hero-copy">
                <p className="eyebrow">Remote sensing intelligence for India</p>
                <h1>Make the planet<br /><em>queryable.</em></h1>
                <p className="hero-lead">A focused workspace for visual questions, radar fusion, spatial grounding, and change intelligence across satellite imagery.</p>
                <div className="hero-actions">
                    <button onClick={onStartExploring} className="primary-cta">Open analysis workspace <FiArrowDownRight /></button>
                    <button onClick={onStartExploring} className="text-cta">Explore capabilities</button>
                </div>
            </div>
            <div className="globe-card">
                <p className="system-label">LIVE COVERAGE MODEL</p>
                <DotGlobe />
                <p className="globe-caption">Drag to rotate the signal field.</p>
            </div>
        </div>
        <div className="capability-strip">
            <p className="system-label">ANALYSIS MODES</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-px bg-[#d9d9dd] border-y border-[#d9d9dd]">
                {FEATURES.map(({ icon: Icon, label, desc, query }) => (
                    <button key={label} onClick={() => onSelectFeature(query)} className="capability-button">
                        <Icon className="text-[#ff7759]" size={19} />
                        <span><b>{label}</b><small>{desc}</small></span>
                        <FiArrowDownRight />
                    </button>
                ))}
            </div>
        </div>
    </section>
);

export default Hero;
