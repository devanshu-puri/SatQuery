import React, { useRef, useEffect, useState } from 'react';
import { MapContainer, TileLayer, FeatureGroup, GeoJSON, ZoomControl, ScaleControl, ImageOverlay, useMap } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { FiLayers, FiChevronDown } from 'react-icons/fi';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';

const FlyToLocation = ({ location }) => {
    const map = useMap();
    useEffect(() => {
        if (location) {
            map.flyTo([location.lat, location.lon], location.zoom || 11);
        }
    }, [location, map]);
    return null;
};

const FitGeoJSONBounds = ({ geojson }) => {
    const map = useMap();
    useEffect(() => {
        if (geojson && geojson.features && geojson.features.length > 0) {
            try {
                const layer = L.geoJSON(geojson);
                const bounds = layer.getBounds();
                if (bounds.isValid()) {
                    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 18, animate: true });
                }
            } catch (e) {
                console.error("Bounds error:", e);
            }
        }
    }, [geojson, map]);
    return null;
};

const FitRasterBounds = ({ bounds }) => {
    const map = useMap();
    useEffect(() => {
        if (bounds && Array.isArray(bounds) && bounds.length === 2 && bounds[0] && bounds[1]) {
            try {
                const [[minLat, minLon], [maxLat, maxLon]] = bounds;
                if (!isNaN(minLat) && !isNaN(minLon) && !isNaN(maxLat) && !isNaN(maxLon)) {
                    map.fitBounds([[minLat, minLon], [maxLat, maxLon]], {
                        padding: [30, 30],
                        maxZoom: 18,
                        animate: true
                    });
                }
            } catch (e) {
                console.error("Failed to fit raster bounds:", e);
            }
        }
    }, [bounds, map]);
    return null;
};

const MapComponent = ({
    onGeometryChange,
    sentinelTileUrl,
    analysisTileUrl,
    analysisIndex,
    flyToLocation,
    visualEvidence,
    uploadedRasterPreview,
    rasterBounds,
    rasterOverlayUrl
}) => {
    const featureGroupRef = useRef();
    const [baseLayer, setBaseLayer] = useState('satellite');
    const [showLabels, setShowLabels] = useState(true);
    const [layerMenuOpen, setLayerMenuOpen] = useState(false);

    const onCreated = (e) => {
        const { layer } = e;
        const geojson = layer.toGeoJSON().geometry;
        onGeometryChange(geojson);
    };

    const onEdited = (e) => {
        const layers = e.layers;
        layers.eachLayer((layer) => {
            const geojson = layer.toGeoJSON().geometry;
            onGeometryChange(geojson);
        });
    };

    const onDeleted = () => {
        onGeometryChange(null);
    };

    // Style for Grounded / Detected GeoJSON Features
    const geojsonStyle = {
        color: '#00F2FE',
        weight: 2.5,
        opacity: 0.9,
        fillColor: '#4FACFE',
        fillOpacity: 0.35,
        dashArray: '4, 4'
    };

    const onEachFeature = (feature, layer) => {
        if (feature.properties) {
            const { label, confidence } = feature.properties;
            layer.bindTooltip(
                `<strong>${label || 'Target'}</strong><br/>Confidence: ${(confidence ? (confidence * 100).toFixed(1) : 90)}%`,
                { permanent: false, direction: 'top' }
            );
        }
    };

    return (
        <div className="relative h-full w-full">
            {/* Map Header Overlay */}
            <div className="absolute top-4 left-4 right-4 z-[1000] flex items-start justify-between gap-2 pointer-events-none">
                <div className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-space-800/90 backdrop-blur-md border border-space-700/60 shadow-xl text-xs font-semibold text-gray-200">
                    <span className="w-2 h-2 rounded-full bg-accent-cyan animate-pulse"></span>
                    <span>ISRO SAC Geospatial Multi-Modal Canvas</span>
                </div>

                <div className="pointer-events-auto relative">
                    <button
                        onClick={() => setLayerMenuOpen(o => !o)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-space-800/90 backdrop-blur-md border border-space-700/60 shadow-xl text-xs font-semibold text-gray-300 hover:text-white transition-colors"
                    >
                        <FiLayers /> Basemap <FiChevronDown />
                    </button>
                    {layerMenuOpen && (
                        <div className="absolute right-0 mt-2 w-44 rounded-xl bg-space-800 border border-space-700/60 shadow-xl p-2 text-xs text-gray-300">
                            <button
                                onClick={() => setBaseLayer('satellite')}
                                className={`w-full text-left px-2 py-1.5 rounded-lg ${baseLayer === 'satellite' ? 'bg-accent-cyan/10 text-accent-cyan' : 'hover:bg-space-700'}`}
                            >
                                Satellite Imagery (Esri)
                            </button>
                            <button
                                onClick={() => setBaseLayer('osm')}
                                className={`w-full text-left px-2 py-1.5 rounded-lg ${baseLayer === 'osm' ? 'bg-accent-cyan/10 text-accent-cyan' : 'hover:bg-space-700'}`}
                            >
                                OpenStreetMap
                            </button>
                            <div className="my-1 border-t border-space-700/60" />
                            <label className="flex items-center gap-2 px-2 py-1.5 cursor-pointer">
                                <input type="checkbox" checked={showLabels} onChange={(e) => setShowLabels(e.target.checked)} />
                                Geographic Labels
                            </label>
                        </div>
                    )}
                </div>
            </div>

            <MapContainer
                center={
                    rasterBounds ? [
                        (rasterBounds[0][0] + rasterBounds[1][0]) / 2,
                        (rasterBounds[0][1] + rasterBounds[1][1]) / 2
                    ] : [12.9830, 77.6210]
                }
                zoom={rasterBounds ? 15 : 13}
                maxZoom={20}
                className="h-full w-full bg-space-900"
                zoomControl={false}
            >
                <FitRasterBounds bounds={rasterBounds} />
                <FlyToLocation location={flyToLocation} />
                {visualEvidence && <FitGeoJSONBounds geojson={visualEvidence} />}

                <ZoomControl position="bottomright" />
                <ScaleControl position="bottomleft" imperial={false} />

                {baseLayer === 'satellite' ? (
                    <TileLayer
                        attribution="Tiles &copy; Esri &mdash; Source: Esri, Maxar, Earthstar Geographics"
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                        maxZoom={20}
                        maxNativeZoom={18}
                        errorTileUrl="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                ) : (
                    <TileLayer
                        attribution='&copy; OpenStreetMap contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        maxZoom={20}
                    />
                )}

                {showLabels && baseLayer === 'satellite' && (
                    <TileLayer
                        url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
                        maxZoom={21}
                    />
                )}

                {/* GEE Sentinel-2 Tile Layer */}
                {sentinelTileUrl && (
                    <TileLayer url={sentinelTileUrl} attribution="Google Earth Engine" maxNativeZoom={16} />
                )}

                {/* GEE Analysis Layer Overlay - Only for genuine web tile URLs */}
                {analysisTileUrl && typeof analysisTileUrl === 'string' && analysisTileUrl.startsWith('http') && (
                    <TileLayer url={analysisTileUrl} opacity={0.75} attribution="GEE Analysis" maxNativeZoom={16} />
                )}

                {/* Satellite GeoTIFF Raster Image Overlay within exact spatial WGS84 bounding box */}
                {rasterBounds && rasterOverlayUrl && (
                    <ImageOverlay
                        url={rasterOverlayUrl}
                        bounds={rasterBounds}
                        opacity={0.88}
                        zIndex={350}
                    />
                )}

                {/* Vector GeoJSON Visual Evidence Overlay (Grounded Bounding Boxes / Change Polygons) */}
                {visualEvidence && (
                    <GeoJSON
                        key={JSON.stringify(visualEvidence)}
                        data={visualEvidence}
                        style={geojsonStyle}
                        onEachFeature={onEachFeature}
                    />
                )}

                <FeatureGroup ref={featureGroupRef}>
                    <EditControl
                        position="topleft"
                        onCreated={onCreated}
                        onEdited={onEdited}
                        onDeleted={onDeleted}
                        draw={{
                            rectangle: true,
                            circle: false,
                            circlemarker: false,
                            marker: false,
                            polyline: false,
                            polygon: {
                                allowIntersection: false,
                                shapeOptions: {
                                    color: '#5BC0BE'
                                }
                            }
                        }}
                    />
                </FeatureGroup>
            </MapContainer>
        </div>
    );
};

export default MapComponent;
