import React from 'react';
import { useMapSelection } from '../../context/MapContext';
import { Layers, Eye } from 'lucide-react';

export function LayerControl() {
  const { activeLayers, toggleLayer } = useMapSelection();

  const layerItems = [
    { key: 'parcels', label: 'Parcels', badgeColor: 'bg-emerald-400' },
    { key: 'buildings', label: 'Buildings', badgeColor: 'bg-slate-400' },
    { key: 'roads', label: 'Roads', badgeColor: 'bg-sky-400' },
    { key: 'flags', label: 'Validation Flags', badgeColor: 'bg-rose-400' },
  ];

  return (
    <div className="bg-white/95 backdrop-blur-md p-4 rounded-2xl border border-pastel-border shadow-pastel-md text-pastel-text space-y-3">
      <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-pastel-muted border-b border-pastel-border pb-2">
        <Layers className="w-4 h-4 text-pastel-action" />
        <span>Layer Explorer</span>
      </div>

      <div className="space-y-1.5">
        {layerItems.map(item => {
          const isActive = activeLayers[item.key];
          return (
            <label
              key={item.key}
              className={`flex items-center justify-between p-2 rounded-xl cursor-pointer transition-all text-xs font-medium ${
                isActive ? 'bg-pastel-lavender/60 text-pastel-text border border-pastel-border' : 'hover:bg-pastel-surface-soft text-pastel-muted'
              }`}
            >
              <div className="flex items-center space-x-2.5">
                <span className={`w-2.5 h-2.5 rounded-full ${item.badgeColor}`} />
                <span>{item.label}</span>
              </div>
              <input
                type="checkbox"
                checked={isActive}
                onChange={() => toggleLayer(item.key)}
                className="rounded border-pastel-border text-pastel-action focus:ring-pastel-action"
              />
            </label>
          );
        })}
      </div>
    </div>
  );
}
