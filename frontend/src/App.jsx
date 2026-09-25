import React, { useState, useEffect, useMemo } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import Sidebar from './components/Sidebar';
import MapComponent from './components/MapComponent';
import ResultsPanel from './components/ResultsPanel';
import ModelCardModal from './components/ModelCardModal';
import SessionHistoryDrawer from './components/SessionHistoryDrawer';
import {
    fetchHealth,
    fetchModels,
    fetchDemoSamples,
    fetchSessionHistory,
    executeQuery,
    fetchGEE
} from './api';

function App() {
    const [healthStatus, setHealthStatus] = useState(null);
    const [models, setModels] = useState({});
    const [isModelsOpen, setIsModelsOpen] = useState(false);
    const [sessionHistory, setSessionHistory] = useState([]);
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

    const [demoSamples, setDemoSamples] = useState([]);
    const [selectedDemoSample, setSelectedDemoSample] = useState(null);

    const [activeMode, setActiveMode] = useState('demo'); // 'demo' | 'upload' | 'gee'
    const [primaryUpload, setPrimaryUpload] = useState(null);
    const [secondaryUpload, setSecondaryUpload] = useState(null);
    const [selectedTaskId, setSelectedTaskId] = useState('single_image_vqa');
    const [query, setQuery] = useState('What is the agricultural and crop condition in this scene?');

    // GEE State
    const [states, setStates] = useState(['Karnataka', 'Maharashtra', 'Tamil Nadu']);
    const [selectedState, setSelectedState] = useState('Karnataka');
    const [areas, setAreas] = useState(['Bengaluru Urban', 'Bengaluru Rural', 'Mysuru', 'Mandya']);
    const [selectedArea, setSelectedArea] = useState('Bengaluru Urban');
    const [geeStartDate, setGeeStartDate] = useState('2024-01-01');
    const [geeEndDate, setGeeEndDate] = useState('2024-09-01');
    const [geeCloudCover, setGeeCloudCover] = useState(20);

    const [geometry, setGeometry] = useState(null);
    const [sentinelData, setSentinelData] = useState(null);
    const [agentResult, setAgentResult] = useState(null);
    const [flyToLocation, setFlyToLocation] = useState(null);

    // Live Streaming State
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamSteps, setStreamSteps] = useState([]);

    useEffect(() => {
        fetchHealth().then(setHealthStatus).catch(() => {});
        fetchModels().then(setModels).catch(() => {});
        fetchDemoSamples().then(res => {
            setDemoSamples(res.samples || []);
            if (res.samples && res.samples.length > 0) {
                setSelectedDemoSample(res.samples[0]);
                setQuery(res.samples[0].query_recommended);
                setSelectedTaskId(res.samples[0].task_recommended);
            }
        }).catch(() => {});
        fetchSessionHistory().then(res => setSessionHistory(res.history || [])).catch(() => {});
    }, []);

    const handleSelectDemoSample = (sample) => {
        setSelectedDemoSample(sample);
        setAgentResult(null);
        setQuery(sample.query_recommended);
        setSelectedTaskId(sample.task_recommended);
        setFlyToLocation(null);
    };

    const handlePrimaryUpload = (uploadData) => {
        setPrimaryUpload(uploadData);
        setAgentResult(null);
        setFlyToLocation(null);
    };

    const handleSecondaryUpload = (uploadData) => {
        setSecondaryUpload(uploadData);
    };

    const handleExploreArea = () => {
        // District centroid coords
        const coords = {
            'Bengaluru Urban': { lat: 12.9830, lon: 77.6210, zoom: 15 },
            'Bengaluru Rural': { lat: 13.2846, lon: 77.5946, zoom: 12 },
            'Mysuru': { lat: 12.2958, lon: 76.6394, zoom: 13 },
            'Mandya': { lat: 12.5242, lon: 76.8958, zoom: 12 },
        };
        const loc = coords[selectedArea] || { lat: 12.9830, lon: 77.6210, zoom: 15 };
        setFlyToLocation(loc);
    };

    const currentRasterBounds = useMemo(() => {
        if (activeMode === 'upload' && primaryUpload?.metadata?.wgs84_bounds) {
            const b = primaryUpload.metadata.wgs84_bounds;
            return [[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]];
        }
        if (activeMode === 'demo' && selectedDemoSample?.primary_metadata?.wgs84_bounds) {
            const b = selectedDemoSample.primary_metadata.wgs84_bounds;
            return [[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]];
        }
        return null;
    }, [activeMode, primaryUpload, selectedDemoSample]);

    const currentRasterPreview = useMemo(() => {
        if (agentResult?.preview_url) {
            return agentResult.preview_url;
        }
        if (activeMode === 'upload') {
            return primaryUpload?.metadata?.preview_url || null;
        }
        if (activeMode === 'demo') {
            return selectedDemoSample?.preview_url || null;
        }
        return null;
    }, [agentResult, activeMode, primaryUpload, selectedDemoSample]);

    const handleAnalyze = async () => {
        if (!query.trim()) {
            alert('Please enter or select a query prompt.');
            return;
        }

        setIsStreaming(true);
        setStreamSteps([
            { step: 'Classifying Query Intent', detail: `Parsing query semantics: "${query}"` },
            { step: 'Validating Input Modality & Format', detail: `Modality: ${activeMode.toUpperCase()} | Format: GeoTIFF/EPSG:4326` }
        ]);

        try {
            // If GEE mode and geometry drawn, fetch live GEE layer
            if (activeMode === 'gee' && geometry) {
                try {
                    const geeRes = await fetchGEE({
                        geometry: geometry,
                        start_date: geeStartDate,
                        end_date: geeEndDate,
                        max_cloud_cover: geeCloudCover,
                        layer_type: 'true_color'
                    });
                    setSentinelData(geeRes);
                } catch (e) {
                    console.log('GEE simulation fallback');
                }
            }

            const payload = {
                query: query,
                session_id: 'default_session',
                demo_sample_id: activeMode === 'demo' ? selectedDemoSample?.id : null,
                primary_upload_id: activeMode === 'upload' ? primaryUpload?.upload_id : null,
                secondary_upload_id: activeMode === 'upload' ? secondaryUpload?.upload_id : null,
                task_mode: selectedTaskId,
                aoi_geometry: geometry
            };

            const result = await executeQuery(payload);
            setAgentResult(result);
            // Refresh history
            fetchSessionHistory().then(res => setSessionHistory(res.history || [])).catch(() => {});
        } catch (error) {
            console.error(error);
            alert('Analysis could not be completed.');
        } finally {
            setIsStreaming(false);
        }
    };

    const handleSelectHistoryItem = (item) => {
        setAgentResult(item);
        setQuery(item.query);
        setSelectedTaskId(item.task_type);
    };

    const handleSelectFeature = (featureQuery) => {
        setQuery(featureQuery);
        document.getElementById('explore')?.scrollIntoView({ behavior: 'smooth' });
    };

    const canAnalyze = Boolean(
        query.trim() && (
            (activeMode === 'demo' && selectedDemoSample) ||
            (activeMode === 'upload' && primaryUpload) ||
            (activeMode === 'gee')
        )
    );

    return (
        <div className="h-screen w-screen overflow-y-auto overflow-x-hidden bg-space-900 flex flex-col">
            <Header
                onOpenModels={() => setIsModelsOpen(true)}
                onOpenHistory={() => setIsHistoryOpen(true)}
                healthStatus={healthStatus}
            />

            <ModelCardModal
                isOpen={isModelsOpen}
                onClose={() => setIsModelsOpen(false)}
                models={models}
            />

            <SessionHistoryDrawer
                isOpen={isHistoryOpen}
                onClose={() => setIsHistoryOpen(false)}
                history={sessionHistory}
                onSelectHistoryItem={handleSelectHistoryItem}
            />

            <Hero
                onStartExploring={() => document.getElementById('explore')?.scrollIntoView({ behavior: 'smooth' })}
                onSelectFeature={handleSelectFeature}
            />

            <section id="explore" className="relative flex flex-row flex-1 min-h-[850px] w-full overflow-hidden border-t border-space-800">
                <Sidebar
                    states={states}
                    selectedState={selectedState}
                    onStateChange={(e) => setSelectedState(e.target.value)}
                    areas={areas}
                    selectedArea={selectedArea}
                    onAreaChange={(e) => setSelectedArea(e.target.value)}
                    onExploreArea={handleExploreArea}
                    query={query}
                    onQueryChange={setQuery}
                    onAnalyze={handleAnalyze}
                    canAnalyze={canAnalyze}
                    activeMode={activeMode}
                    onModeChange={setActiveMode}
                    primaryUpload={primaryUpload}
                    onPrimaryUpload={handlePrimaryUpload}
                    secondaryUpload={secondaryUpload}
                    onSecondaryUpload={handleSecondaryUpload}
                    selectedTaskId={selectedTaskId}
                    onSelectTaskId={setSelectedTaskId}
                    demoSamples={demoSamples}
                    selectedDemoSample={selectedDemoSample}
                    onSelectDemoSample={handleSelectDemoSample}
                    geeStartDate={geeStartDate}
                    onGeeStartDateChange={setGeeStartDate}
                    geeEndDate={geeEndDate}
                    onGeeEndDateChange={setGeeEndDate}
                    geeCloudCover={geeCloudCover}
                    onGeeCloudCoverChange={setGeeCloudCover}
                />

                <div className="relative flex-1 w-1/2 h-full p-3">
                    <div className="h-full w-full overflow-hidden rounded-2xl shadow-2xl ring-1 ring-space-700/60">
                        <MapComponent
                            onGeometryChange={setGeometry}
                            sentinelTileUrl={sentinelData?.tile_url}
                            analysisTileUrl={sentinelData?.analysis_tile_url || null}
                            analysisIndex={agentResult?.task_type}
                            flyToLocation={flyToLocation}
                            visualEvidence={agentResult?.visual_evidence}
                            rasterBounds={currentRasterBounds}
                            rasterOverlayUrl={currentRasterPreview}
                        />
                    </div>
                </div>

                <ResultsPanel
                    query={query}
                    sentinelData={sentinelData}
                    agentResult={agentResult}
                    primaryUpload={primaryUpload}
                    secondaryUpload={secondaryUpload}
                    selectedDemoSample={selectedDemoSample}
                    isStreaming={isStreaming}
                    streamSteps={streamSteps}
                />
            </section>
        </div>
    );
}

export default App;
