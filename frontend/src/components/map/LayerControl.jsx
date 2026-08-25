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
    <div className="cv-panel-elevated space-y-3 rounded-2xl p-4 text-pastel-text transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_16px_40px_rgba(1,28,64,0.12)]">
      <div className="flex items-center space-x-2 border-b border-[#C9E5EE] pb-2 text-xs font-bold uppercase tracking-[0.18em] text-[#4F7285]">
        <Layers className="h-4 w-4 text-[#266580]" />
        <span>Layer Explorer</span>
      </div>

      <div className="space-y-1.5">
        {layerItems.map(item => {
          const isActive = activeLayers[item.key];
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
                <span>{item.label}</span>
              </div>
              <input
                type="checkbox"
                checked={isActive}
                onChange={() => toggleLayer(item.key)}
                className="rounded border-[#C9E5EE] text-[#266580] focus:ring-[#54ACBF]"
              />
            </label>
          );
        })}
      </div>
    </div>
  );
}
