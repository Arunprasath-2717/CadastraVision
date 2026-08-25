import React, { useState } from 'react';
import { useMapSelection } from '../../context/MapContext';
import { Layers, RefreshCw, Building2, Navigation, Wheat, Flag, Globe, Database } from 'lucide-react';

export function LayerControl() {
  const { activeLayers, toggleLayer } = useMapSelection();
  const [loadingLayer, setLoadingLayer] = useState(null);

  const layerItems = [
    { key: 'parcels', label: 'Parcels (Land Records)', icon: Database, badgeColor: 'bg-emerald-400' },
    { key: 'fields', label: 'Agricultural Fields', icon: Wheat, badgeColor: 'bg-amber-400' },
    { key: 'buildings', label: 'Buildings & Structures', icon: Building2, badgeColor: 'bg-slate-400' },
    { key: 'roads', label: 'Road Networks', icon: Navigation, badgeColor: 'bg-sky-400' },
    { key: 'flags', label: 'Validation Flags', icon: Flag, badgeColor: 'bg-rose-400' },
    { key: 'openfreemap', label: 'OpenFreeMap Vector', icon: Globe, badgeColor: 'bg-indigo-400' },
    { key: 'overpass', label: 'Overpass OSM Overlay', icon: RefreshCw, badgeColor: 'bg-pink-400' },
  ];

  const handleReloadLayers = (layerKey) => {
    setLoadingLayer(layerKey || 'all');
    window.dispatchEvent(new CustomEvent('cadastra:refresh-map-layers', { detail: { layer: layerKey } }));
    setTimeout(() => {
      setLoadingLayer(null);
    }, 600);
  };

  return (
    <div className="cv-panel-elevated space-y-3 rounded-2xl p-4 text-pastel-text transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_40px_rgba(1,28,64,0.12)]">
      <div className="flex items-center justify-between border-b border-[#C9E5EE] pb-2">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-[0.18em] text-[#4F7285]">
          <Layers className="h-4 w-4 text-[#266580]" />
          <span>GIS Layer Controls</span>
        </div>
        <button
          onClick={() => handleReloadLayers(null)}
          title="Reload All Layers"
          aria-label="Reload All Layers"
          className="flex items-center gap-1.5 rounded-lg border border-[#A7EBF2]/40 bg-white/80 px-2 py-1 text-[10px] font-mono font-medium text-[#266580] transition-colors hover:border-[#54ACBF] hover:bg-sky-50"
        >
          <RefreshCw className={`h-3 w-3 ${loadingLayer === 'all' ? 'animate-spin' : ''}`} />
          <span>Reload</span>
        </button>
      </div>

      {/* Layer Toggle List */}
      <div className="space-y-1.5">
        {layerItems.map(item => {
          const isActive = activeLayers[item.key];
          const IconComp = item.icon;

          return (
            <label
              key={item.key}
              className={`flex cursor-pointer items-center justify-between rounded-xl p-2.5 text-xs font-medium transition-all duration-200 ${
                isActive
                  ? 'border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.22),rgba(84,172,191,0.08))] text-[#011C40] shadow-[0_8px_20px_rgba(2,56,89,0.06)]'
                  : 'text-[#4F7285] hover:border hover:border-[#A7EBF2]/60 hover:bg-[linear-gradient(135deg,rgba(167,235,242,0.14),rgba(84,172,191,0.04))]'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span className={`h-2.5 w-2.5 rounded-full ${item.badgeColor}`} />
                <IconComp className="h-3.5 w-3.5 text-[#266580]" />
                <span>{item.label}</span>
              </div>
              <input
                type="checkbox"
                checked={Boolean(isActive)}
                onChange={() => toggleLayer(item.key)}
                className="rounded border-[#C9E5EE] text-[#266580] focus:ring-[#54ACBF]"
              />
            </label>
          );
        })}
      </div>

      {/* Quick Action Load Layer Buttons */}
      <div className="pt-2 border-t border-[#C9E5EE] space-y-1.5">
        <div className="text-[10px] font-mono font-bold uppercase tracking-[0.18em] text-[#4F7285]">
          Quick Data Loaders
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          <button
            onClick={() => handleReloadLayers('buildings')}
            className="flex flex-col items-center justify-center rounded-xl border border-[#C9E5EE] bg-white/70 p-2 text-center transition-all hover:border-[#54ACBF] hover:bg-sky-50"
          >
            <Building2 className="h-4 w-4 text-slate-600 mb-1" />
            <span className="text-[10px] font-semibold text-[#011C40]">Buildings</span>
          </button>

          <button
            onClick={() => handleReloadLayers('roads')}
            className="flex flex-col items-center justify-center rounded-xl border border-[#C9E5EE] bg-white/70 p-2 text-center transition-all hover:border-[#54ACBF] hover:bg-sky-50"
          >
            <Navigation className="h-4 w-4 text-sky-600 mb-1" />
            <span className="text-[10px] font-semibold text-[#011C40]">Roads</span>
          </button>

          <button
            onClick={() => handleReloadLayers('fields')}
            className="flex flex-col items-center justify-center rounded-xl border border-[#C9E5EE] bg-white/70 p-2 text-center transition-all hover:border-[#54ACBF] hover:bg-sky-50"
          >
            <Wheat className="h-4 w-4 text-amber-600 mb-1" />
            <span className="text-[10px] font-semibold text-[#011C40]">Fields</span>
          </button>
        </div>
      </div>
    </div>
  );
}
