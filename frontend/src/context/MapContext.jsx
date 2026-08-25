import React, { createContext, useContext, useState, useCallback } from 'react';
import { parcelApi } from '../services/parcelApi';
import { validationApi } from '../services/validationApi';

const MapContext = createContext(null);

export function MapProvider({ children }) {
  const [selectedParcelId, setSelectedParcelId] = useState(null);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [basemap, setBasemap] = useState('openfreemap');
  const [activeLayers, setActiveLayers] = useState({
    parcels: true,
    buildings: true,
    roads: true,
    flags: true,
    openfreemap: true,
    overpass: true,
  });

  const [isReviewQueueOpen, setIsReviewQueueOpen] = useState(true);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedGeometry, setEditedGeometry] = useState(null);
  
  const [revalidationState, setRevalidationState] = useState({
    isRevalidating: false,
    result: null,
  });

  const [gisConflict, setGisConflict] = useState(null);
  const [mapInstance, setMapInstance] = useState(null);

  /**
   * Select parcel and synchronize Map + Inspector + Review Queue
   */
  const selectParcel = useCallback(async (parcelId, flyTo = true) => {
    setSelectedParcelId(parcelId);
    if (!parcelId) {
      setSelectedParcel(null);
      setIsInspectorOpen(false);
      setIsEditing(false);
      return;
    }

    const parcelData = await parcelApi.getParcelById(parcelId);
    if (parcelData) {
      setSelectedParcel(parcelData);
      setIsInspectorOpen(true);

      if (parcelData.gis_conflict) {
        setGisConflict(parcelData.gis_conflict);
      } else {
        setGisConflict(null);
      }

      if (flyTo && mapInstance && parcelData.geometry) {
        try {
          // Calculate centroid / bbox for smooth zoom
          const coords = parcelData.geometry.coordinates[0];
          let minLng = Infinity, maxLng = -Infinity, minLat = Infinity, maxLat = -Infinity;
          coords.forEach(([lng, lat]) => {
            if (lng < minLng) minLng = lng;
            if (lng > maxLng) maxLng = lng;
            if (lat < minLat) minLat = lat;
            if (lat > maxLat) maxLat = lat;
          });
          
          mapInstance.fitBounds(
            [[minLng - 0.0005, minLat - 0.0005], [maxLng + 0.0005, maxLat + 0.0005]],
            { padding: 80, duration: 1200 }
          );
        } catch (e) {
          console.warn('Map zoom calculation failed:', e);
        }
      }
    }
  }, [mapInstance]);

  /**
   * Toggle Map Layer visibility
   */
  const toggleLayer = useCallback((layerKey) => {
    setActiveLayers(prev => ({
      ...prev,
      [layerKey]: !prev[layerKey]
    }));
  }, []);

  /**
   * Start Interactive Boundary Editing
   */
  const startEditing = useCallback(() => {
    if (!selectedParcel) return;
    setIsEditing(true);
    setEditedGeometry(JSON.parse(JSON.stringify(selectedParcel.geometry)));
    setRevalidationState({ isRevalidating: false, result: null });
  }, [selectedParcel]);

  /**
   * Cancel Editing
   */
  const cancelEditing = useCallback(() => {
    setIsEditing(false);
    setEditedGeometry(null);
    setRevalidationState({ isRevalidating: false, result: null });
  }, []);

  /**
   * Save Edited Geometry and Trigger Server Re-validation (PRD Section 4.4 & Section 22)
   */
  const saveEditedGeometry = useCallback(async (newGeo) => {
    if (!selectedParcelId) return;

    setRevalidationState({ isRevalidating: true, result: null });

    // Simulate Server Revalidation network delay
    setTimeout(async () => {
      const res = await parcelApi.editParcel(selectedParcelId, newGeo || editedGeometry);
      setRevalidationState({ isRevalidating: false, result: res.revalidation });
      
      // Update selected parcel with edited status
      const updated = await parcelApi.getParcelById(selectedParcelId);
      setSelectedParcel(updated);
      setIsEditing(false);
      
      // Remove resolved items from review queue
      validationApi.removeFromQueue(selectedParcelId);
    }, 1500);
  }, [selectedParcelId, editedGeometry]);

  /**
   * Approve Current Parcel
   */
  const approveCurrentParcel = useCallback(async () => {
    if (!selectedParcelId) return;
    const res = await parcelApi.approveParcel(selectedParcelId);
    if (res.success) {
      const updated = await parcelApi.getParcelById(selectedParcelId);
      setSelectedParcel(updated);
      validationApi.removeFromQueue(selectedParcelId);
    }
    return res;
  }, [selectedParcelId]);

  /**
   * Reject Current Parcel
   */
  const rejectCurrentParcel = useCallback(async (reason) => {
    if (!selectedParcelId) return;
    const res = await parcelApi.rejectParcel(selectedParcelId, 'USR-4092', reason);
    if (res.success) {
      const updated = await parcelApi.getParcelById(selectedParcelId);
      setSelectedParcel(updated);
    }
    return res;
  }, [selectedParcelId]);

  return (
    <MapContext.Provider value={{
      selectedParcelId,
      selectedParcel,
      selectParcel,
      activeLayers,
      toggleLayer,
      isReviewQueueOpen,
      setIsReviewQueueOpen,
      isInspectorOpen,
      setIsInspectorOpen,
      isEditing,
      startEditing,
      cancelEditing,
      editedGeometry,
      setEditedGeometry,
      saveEditedGeometry,
      revalidationState,
      approveCurrentParcel,
      rejectCurrentParcel,
      gisConflict,
      setGisConflict,
      mapInstance,
      setMapInstance,
      basemap,
      setBasemap
    }}>
      {children}
    </MapContext.Provider>
  );
}

export function useMapSelection() {
  const context = useContext(MapContext);
  if (!context) {
    throw new Error('useMapSelection must be used within a MapProvider');
  }
  return context;
}
