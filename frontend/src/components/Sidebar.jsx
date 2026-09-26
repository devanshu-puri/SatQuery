import React, { useState } from 'react';
import { FiMapPin, FiUploadCloud, FiPlay } from 'react-icons/fi';
import { uploadRasterFile } from '../api';

const Sidebar = ({
    states, selectedState, onStateChange, areas, selectedArea, onAreaChange,
    onExploreArea, activeMode, onModeChange, primaryUpload, onPrimaryUpload,
    secondaryUpload, onSecondaryUpload, demoSamples, selectedDemoSample,
    onSelectDemoSample, geeStartDate, onGeeStartDateChange, geeEndDate,
    onGeeEndDateChange, geeCloudCover, onGeeCloudCoverChange
}) => {
    const [uploadingPrimary, setUploadingPrimary] = useState(false);
    const [uploadingSecondary, setUploadingSecondary] = useState(false);

    const upload = async (event, setLoading, onComplete) => {
        const file = event.target.files?.[0];
        if (!file) return;
        setLoading(true);
        try {
            onComplete(await uploadRasterFile(file));
        } catch (error) {
            console.error(error);
            alert('The raster could not be validated. Please choose a supported GeoTIFF or image.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <aside className="source-panel" aria-label="Imagery source">
            <div className="source-tabs" role="tablist" aria-label="Source mode">
                <button title="Demo scenes" onClick={() => onModeChange('demo')} className={activeMode === 'demo' ? 'is-active' : ''}><FiPlay /><span>Demo</span></button>
                <button title="Upload imagery" onClick={() => onModeChange('upload')} className={activeMode === 'upload' ? 'is-active' : ''}><FiUploadCloud /><span>Upload</span></button>
                <button title="Live AOI" onClick={() => onModeChange('gee')} className={activeMode === 'gee' ? 'is-active' : ''}><FiMapPin /><span>AOI</span></button>
            </div>

            {activeMode === 'demo' && (
                <div className="source-content">
                    <p className="panel-kicker">Demo scene</p>
                    <div className="sample-list">
                        {demoSamples.map((sample) => (
                            <button key={sample.id} onClick={() => onSelectDemoSample(sample)} className={selectedDemoSample?.id === sample.id ? 'sample is-selected' : 'sample'}>
                                <strong>{sample.title}</strong><span>{sample.provenance}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {activeMode === 'upload' && (
                <div className="source-content">
                    <p className="panel-kicker">Validated imagery</p>
                    <label className="upload-slot"><FiUploadCloud /><span><strong>Primary image</strong><small>Optical image or T1</small></span><input type="file" accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" onChange={(event) => upload(event, setUploadingPrimary, onPrimaryUpload)} /></label>
                    {uploadingPrimary && <p className="source-status">Checking primary image...</p>}
                    {primaryUpload?.metadata && <p className="file-status">{primaryUpload.metadata.filename}<br />{primaryUpload.metadata.modality} · {primaryUpload.metadata.crs}</p>}
                    <label className="upload-slot"><FiUploadCloud /><span><strong>Secondary image</strong><small>T2 or matching SAR</small></span><input type="file" accept=".tif,.tiff,.geotiff,.png,.jpg,.jpeg" onChange={(event) => upload(event, setUploadingSecondary, onSecondaryUpload)} /></label>
                    {uploadingSecondary && <p className="source-status">Checking secondary image...</p>}
                    {secondaryUpload?.metadata && <p className="file-status">{secondaryUpload.metadata.filename}<br />{secondaryUpload.metadata.modality}</p>}
                </div>
            )}

            {activeMode === 'gee' && (
                <div className="source-content compact-form">
                    <p className="panel-kicker">Live AOI</p>
                    <label>State<select value={selectedState} onChange={onStateChange}>{states.map((state) => <option key={state}>{state}</option>)}</select></label>
                    <label>District<select value={selectedArea} onChange={onAreaChange}>{areas.map((area) => <option key={area}>{area}</option>)}</select></label>
                    <div className="date-grid"><label>From<input type="date" value={geeStartDate} onChange={(event) => onGeeStartDateChange(event.target.value)} /></label><label>To<input type="date" value={geeEndDate} onChange={(event) => onGeeEndDateChange(event.target.value)} /></label></div>
                    <label>Cloud cover <b>{geeCloudCover}%</b><input type="range" min="0" max="50" value={geeCloudCover} onChange={(event) => onGeeCloudCoverChange(Number(event.target.value))} /></label>
                    <button className="outline-action" onClick={onExploreArea}>Center map</button>
                </div>
            )}
            <p className="source-footnote">The agent selects its workflow from your language, request, imagery type, and selected area.</p>
        </aside>
    );
};

export default Sidebar;
