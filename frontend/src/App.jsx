import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Upload, 
  Database, 
  Settings, 
  Shield, 
  ChevronDown, 
  ChevronUp, 
  MapPin, 
  CheckCircle, 
  AlertTriangle, 
  Play, 
  Trash2, 
  Download, 
  Eye, 
  Activity,
  Layers,
  Sparkles,
  Info,
  Clock,
  HardDrive
} from 'lucide-react';
import './App.css';

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [backend, setBackend] = useState('samgeo');
  const [chunkSize, setChunkSize] = useState(512);
  const [overlap, setOverlap] = useState(64);
  const [isDragActive, setIsDragActive] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [activeRun, setActiveRun] = useState(null);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [paramsExpanded, setParamsExpanded] = useState(false);
  const [globalStats, setGlobalStats] = useState({
    queriesCount: 0,
    parcelsCount: 0,
    averageConfidence: 0.0
  });

  const fileInputRef = useRef(null);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const geojsonLayerRef = useRef(null);
  const imageOverlayRef = useRef(null);

  // Fetch past query logs and compute global stats
  const fetchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history`);
      if (response.ok) {
        const data = await response.json();
        setHistoryList(data);
        
        // Calculate global statistics
        if (data.length > 0) {
          const totalParcels = data.reduce((acc, curr) => acc + (curr.parcel_count || 0), 0);
          const validConfidenceList = data.filter(d => d.avg_confidence > 0);
          const avgConf = validConfidenceList.length > 0 
            ? (validConfidenceList.reduce((acc, curr) => acc + curr.avg_confidence, 0) / validConfidenceList.length).toFixed(1)
            : 0.0;
          
          setGlobalStats({
            queriesCount: data.length,
            parcelsCount: totalParcels,
            averageConfidence: parseFloat(avgConf)
          });
        } else {
          setGlobalStats({
            queriesCount: 0,
            parcelsCount: 0,
            averageConfidence: 0.0
          });
        }
      }
    } catch (err) {
      console.error("Failed to fetch query logs history:", err);
    }
  };

  // Initialize Map
  useEffect(() => {
    if (!mapInstanceRef.current && mapRef.current) {
      // Initialize map instance
      const map = L.map(mapRef.current, {
        center: [20.5937, 78.9629], // Center of India
        zoom: 5,
        zoomControl: true,
      });

      // Add base layer: Esri World Imagery (Satellite)
      const satelliteLayer = L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
          maxZoom: 19,
          attribution: 'Tiles &copy; Esri &mdash; Esri World Imagery'
        }
      ).addTo(map);

      // Standard OSM layer as fallback
      const streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{y}/{x}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap contributors'
      });

      // Add layer controllers
      L.control.layers({
        "Satellite Imagery": satelliteLayer,
        "Street Maps": streetLayer,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    fetchHistory();

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update map when activeRun changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !activeRun) return;

    // 1. Remove previous overlays
    if (geojsonLayerRef.current) {
      map.removeLayer(geojsonLayerRef.current);
      geojsonLayerRef.current = null;
    }
    if (imageOverlayRef.current) {
      map.removeLayer(imageOverlayRef.current);
      imageOverlayRef.current = null;
    }

    // 2. Render bounding box image overlay
    if (activeRun.bbox) {
      const bounds = activeRun.bbox; // Format: [[lat_min, lng_min], [lat_max, lng_max]]
      const imageUrl = `${API_BASE_URL}/static/visualizations/${activeRun.id}.png`;

      // Use a timestamp bypass cache to reload fresh files
      const overlay = L.imageOverlay(`${imageUrl}?t=${Date.now()}`, bounds, {
        opacity: 0.85,
        interactive: false,
      }).addTo(map);

      imageOverlayRef.current = overlay;

      // Fit map bounds to the image area if no vector feature exists
      if (!activeRun.geojson || !activeRun.geojson.features || activeRun.geojson.features.length === 0) {
        map.fitBounds(bounds, { padding: [30, 30] });
      }
    }

    // 3. Render vector geometries (yellow lines)
    if (activeRun.geojson && activeRun.geojson.features && activeRun.geojson.features.length > 0) {
      const geojsonLayer = L.geoJSON(activeRun.geojson, {
        style: {
          color: '#00ffff', // High contrast cyber-cyan borders on map
          weight: 2,
          opacity: 0.9,
          fillColor: '#00ffff',
          fillOpacity: 0.1,
        },
        onEachFeature: (feature, layer) => {
          layer.on('click', () => {
            setSelectedParcel(feature);
          });
          layer.bindTooltip(
            `Confidence: ${feature.properties.confidence}%`,
            { permanent: false, direction: 'top' }
          );
        }
      }).addTo(map);

      geojsonLayerRef.current = geojsonLayer;
      
      // Fit maps viewport coordinates
      map.fitBounds(geojsonLayer.getBounds(), { padding: [30, 30] });
    }
  }, [activeRun]);

  // Load a past query run from history log
  const loadRun = async (queryId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history/${queryId}`);
      if (response.ok) {
        const data = await response.json();
        setActiveRun(data);
        setSelectedParcel(null);
        setActiveTab('upload'); // Switch tab to view current active selection stats
      } else {
        alert("Failed to retrieve query run details from database.");
      }
    } catch (err) {
      console.error(err);
      alert("Network error fetching query details.");
    }
  };

  // Delete a query run
  const deleteRun = async (queryId, e) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this query run? This will delete all stored vector shapes from database.")) {
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/history/${queryId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        if (activeRun && activeRun.id === queryId) {
          setActiveRun(null);
          setSelectedParcel(null);
          // Reset map
          if (geojsonLayerRef.current && mapInstanceRef.current) {
            mapInstanceRef.current.removeLayer(geojsonLayerRef.current);
            geojsonLayerRef.current = null;
          }
          if (imageOverlayRef.current && mapInstanceRef.current) {
            mapInstanceRef.current.removeLayer(imageOverlayRef.current);
            imageOverlayRef.current = null;
          }
        }
        fetchHistory();
      }
    } catch (err) {
      console.error(err);
      alert("Failed to delete log entry.");
    }
  };

  // Download GeoJSON
  const downloadGeoJSON = (queryId, e) => {
    e.stopPropagation();
    fetch(`${API_BASE_URL}/api/history/${queryId}`)
      .then(res => res.json())
      .then(data => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(jsonPrettyString(data.geojson));
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute("href", dataStr);
        downloadAnchor.setAttribute("download", `${data.filename}_parcels.geojson`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
      })
      .catch(err => {
        console.error(err);
        alert("Failed to download GeoJSON.");
      });
  };

  const jsonPrettyString = (obj) => {
    return JSON.stringify(obj, null, 2);
  };

  // File drag & drop event triggers
  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => {
    setIsDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragActive(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const triggerFileSelect = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  // Handle the live neural network segmentation request
  const handleFileUpload = async (file) => {
    if (isProcessing) return;

    // Validate that it's a GeoTIFF (by extension)
    const ext = file.name.split('.').pop().toLowerCase();
    if (ext !== 'tif' && ext !== 'tiff') {
      alert("Invalid format! Please upload a valid GeoTIFF raster (.tif or .tiff) file.");
      return;
    }

    setIsProcessing(true);
    setProgress(10);
    setStatusMessage("Uploading GeoTIFF raster image to server...");

    // Mock progress ticker for user responsiveness
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 5;
      });
    }, 1500);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("backend", backend);
    formData.append("chunk_size", chunkSize);
    formData.append("overlap", overlap);

    try {
      setStatusMessage("Running windowed neural inference. Detecting rooftops...");
      const response = await fetch(`${API_BASE_URL}/api/segment`, {
        method: "POST",
        body: formData,
      });

      clearInterval(interval);

      if (response.ok) {
        setProgress(100);
        setStatusMessage("Parsing vector features & saving cadastra log database...");
        const result = await response.json();
        
        setTimeout(() => {
          setIsProcessing(false);
          setActiveRun(result);
          setSelectedParcel(null);
          fetchHistory();
        }, 800);
      } else {
        const errDetail = await response.text();
        throw new Error(errDetail || "Inference server error");
      }
    } catch (err) {
      clearInterval(interval);
      setIsProcessing(false);
      setProgress(0);
      setStatusMessage("");
      console.error(err);
      alert(`Segmentation failed: ${err.message}`);
    }
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Filter logs list based on search term
  const filteredHistory = historyList.filter(item => 
    item.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="dashboard-container">
      {/* LEFT SIDEBAR PANEL */}
      <div className="sidebar">
        
        {/* Logo and branding */}
        <div className="sidebar-header">
          <Layers className="logo-icon" size={24} />
          <h1>CadastraVision</h1>
        </div>

        {/* Tab Controls */}
        <div className="tabs-nav">
          <button 
            className={`tab-btn ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            <Upload size={16} />
            Upload & Run
          </button>
          <button 
            className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            <Database size={16} />
            History Log
          </button>
        </div>

        {/* Main Tab Panels Content */}
        <div className="panel-content">
          
          {activeTab === 'upload' ? (
            <>
              {/* Parameter Settings (Accordion) */}
              <div className="glass-panel parameters-card">
                <div 
                  className="parameters-header" 
                  onClick={() => setParamsExpanded(!paramsExpanded)}
                >
                  <h3>
                    <Settings size={16} className="logo-icon" />
                    Model & Inference Configuration
                  </h3>
                  {paramsExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>

                {paramsExpanded && (
                  <div className="parameters-body">
                    <div className="form-group">
                      <label>AI Segmentation Model</label>
                      <select 
                        value={backend} 
                        onChange={(e) => setBackend(e.target.value)}
                        className="form-input"
                      >
                        <option value="samgeo">SAMGeo (Segment Anything Geospatial)</option>
                        <option value="fastsam">FastSAM (Lightweight Instance Segmenter)</option>
                        <option value="yolov8">YOLOv8-seg (Fast Fallback)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Tile Window Chunk Size (pixels)</label>
                      <input 
                        type="number" 
                        value={chunkSize} 
                        onChange={(e) => setChunkSize(parseInt(e.target.value))}
                        className="form-input" 
                        min="256" 
                        max="1024"
                        step="128"
                      />
                    </div>

                    <div className="form-group">
                      <label>Window Overlap stride (pixels)</label>
                      <input 
                        type="number" 
                        value={overlap} 
                        onChange={(e) => setOverlap(parseInt(e.target.value))}
                        className="form-input" 
                        min="0" 
                        max="256"
                        step="16"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Upload Dropper */}
              {!isProcessing && (
                <div 
                  className={`dropzone ${isDragActive ? 'drag-active' : ''}`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={triggerFileSelect}
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={handleFileChange} 
                    accept=".tif,.tiff" 
                    style={{ display: 'none' }} 
                  />
                  <Upload size={40} className="dropzone-icon" />
                  <div>
                    <p style={{ fontWeight: '500', marginBottom: '4px' }}>Drag & Drop Drone GeoTIFF</p>
                    <p style={{ fontSize: '12px' }}>or <span className="browse-text">browse local files</span></p>
                  </div>
                  <div className="status-message" style={{ color: 'var(--text-muted)', fontSize: '11px' }}>
                    <Shield size={12} />
                    Zero-PII Compliance Guaranteed
                  </div>
                </div>
              )}

              {/* Active Neural Network Processing Loader */}
              {isProcessing && (
                <div className="glass-panel progress-card">
                  <div className="progress-header">
                    <span className="progress-title">Segmenting Image</span>
                    <span className="progress-percentage">{progress}%</span>
                  </div>
                  <div className="progress-bar-bg">
                    <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
                  </div>
                  <div className="status-message">
                    <span className="spinner"></span>
                    {statusMessage}
                  </div>
                </div>
              )}

              {/* Selection & Parcel Metrics Summary */}
              {activeRun && (
                <div className="glass-panel selection-stats">
                  <h3>Active Footprints Stats</h3>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <div className="stat-label">File Name</div>
                      <div className="stat-value" style={{ fontSize: '12px', wordBreak: 'break-all' }}>{activeRun.filename}</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-label">AI Backend</div>
                      <div className="stat-value" style={{ textTransform: 'capitalize' }}>{activeRun.backend}</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-label">Footprints Detected</div>
                      <div className="stat-value">{activeRun.geojson.features.length}</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-label">Mean Confidence</div>
                      <div className="stat-value">{activeRun.avg_confidence ? `${activeRun.avg_confidence}%` : 'N/A'}</div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-label">Time Taken</div>
                      <div className="stat-value" style={{ fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
                        {(activeRun.duration_ms / 1000).toFixed(2)}s
                      </div>
                    </div>
                    <div className="stat-item">
                      <div className="stat-label">File Size</div>
                      <div className="stat-value" style={{ fontSize: '13px' }}>{formatBytes(activeRun.file_size)}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Parcel Inspector inside tab */}
              {selectedParcel && (
                <div className="glass-panel parcel-inspector">
                  <div className="inspector-header">
                    <div className="inspector-title">
                      <Sparkles size={16} />
                      Parcel Footprint #{selectedParcel.properties.id}
                    </div>
                    <button 
                      className="close-inspector-btn"
                      onClick={() => setSelectedParcel(null)}
                    >
                      &times;
                    </button>
                  </div>
                  
                  <div className="metric-bar-group">
                    <div className="metric-row">
                      <div className="metric-label-row">
                        <span className="metric-name">Detection Confidence</span>
                        <span className="metric-val">{selectedParcel.properties.confidence}%</span>
                      </div>
                      <div className="metric-track">
                        <div 
                          className="metric-fill" 
                          style={{ width: `${selectedParcel.properties.confidence}%`, background: 'var(--primary)' }}
                        ></div>
                      </div>
                    </div>

                    <div className="metric-row">
                      <div className="metric-label-row">
                        <span className="metric-name">Rooftop Regularity</span>
                        <span className="metric-val">{(selectedParcel.properties.confidence_breakdown.regularity * 100).toFixed(0)}%</span>
                      </div>
                      <div className="metric-track">
                        <div 
                          className="metric-fill" 
                          style={{ width: `${selectedParcel.properties.confidence_breakdown.regularity * 100}%`, background: 'var(--secondary)' }}
                        ></div>
                      </div>
                    </div>

                    <div className="metric-row">
                      <div className="metric-label-row">
                        <span className="metric-name">Compactness Metric</span>
                        <span className="metric-val">{(selectedParcel.properties.confidence_breakdown.compactness * 100).toFixed(0)}%</span>
                      </div>
                      <div className="metric-track">
                        <div 
                          className="metric-fill" 
                          style={{ width: `${selectedParcel.properties.confidence_breakdown.compactness * 100}%`, background: 'var(--accent-yellow)' }}
                        ></div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginTop: '6px', color: 'var(--text-muted)' }}>
                      <span>Vertices: {selectedParcel.properties.confidence_breakdown.vertex_count}</span>
                      <span>Tile x,y: {selectedParcel.properties.tile_coords ? `${selectedParcel.properties.tile_coords[0]},${selectedParcel.properties.tile_coords[1]}` : 'N/A'}</span>
                    </div>
                  </div>
                </div>
              )}

              {!activeRun && !selectedParcel && (
                <div className="empty-state">
                  <MapPin className="empty-state-icon" size={32} />
                  <p>No active dataset loaded on map. Upload a raster file above or choose from your history logs log.</p>
                </div>
              )}
            </>
          ) : (
            
            /* HISTORY TAB */
            <div className="history-list">
              <div className="search-bar">
                <input 
                  type="text" 
                  placeholder="Filter by file name..." 
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', flex: '1' }}>
                {filteredHistory.length > 0 ? (
                  filteredHistory.map((item) => (
                    <div 
                      key={item.id} 
                      className={`glass-panel log-item ${activeRun && activeRun.id === item.id ? 'active' : ''}`}
                      onClick={() => loadRun(item.id)}
                      style={{ cursor: 'pointer', borderLeft: activeRun && activeRun.id === item.id ? '3px solid var(--primary)' : '1px solid var(--border-color)' }}
                    >
                      <div className="log-item-header">
                        <div className="log-title">{item.filename}</div>
                        <div className="log-date">{new Date(item.created_at).toLocaleDateString()}</div>
                      </div>

                      <div className="log-meta">
                        <span className={`log-badge ${item.backend}`}>{item.backend}</span>
                        <span>Parcels: <strong>{item.parcel_count}</strong></span>
                        <span>Avg Conf: <strong>{item.avg_confidence ? `${item.avg_confidence}%` : 'N/A'}</strong></span>
                        <span>Size: <strong>{formatBytes(item.file_size)}</strong></span>
                      </div>

                      <div className="log-actions">
                        <button 
                          className="action-btn primary-action"
                          onClick={() => loadRun(item.id)}
                        >
                          <Eye size={12} />
                          Load on Map
                        </button>
                        <button 
                          className="action-btn"
                          onClick={(e) => downloadGeoJSON(item.id, e)}
                        >
                          <Download size={12} />
                          GeoJSON
                        </button>
                        <button 
                          className="action-btn danger-action"
                          onClick={(e) => deleteRun(item.id, e)}
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="no-history-msg">No historical runs match your query.</div>
                )}
              </div>
            </div>
          )}

        </div>

        {/* Global stats block at bottom */}
        <div className="sidebar-footer">
          <div className="global-stat-row">
            <span>Total Query Runs</span>
            <span className="global-stat-val">{globalStats.queriesCount}</span>
          </div>
          <div className="global-stat-row">
            <span>Total Building Shapes</span>
            <span className="global-stat-val">{globalStats.parcelsCount}</span>
          </div>
          <div className="global-stat-row">
            <span>Mean Confidence Database</span>
            <span className="global-stat-val">{globalStats.averageConfidence}%</span>
          </div>
        </div>

      </div>

      {/* RIGHT FULL SCREEN MAP */}
      <div className="map-panel">
        {isProcessing && (
          <div className="map-loading-overlay">
            <span className="spinner"></span>
            Running CNN Footprint Extraction...
          </div>
        )}
        <div id="map" className="map-container" ref={mapRef}></div>
      </div>
    </div>
  );
}

export default App;
