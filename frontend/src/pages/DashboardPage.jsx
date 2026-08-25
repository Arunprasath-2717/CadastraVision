import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMapSelection } from '../context/MapContext';
import { MapView } from '../components/map/MapView';
import { LayerControl } from '../components/map/LayerControl';
import { MapLegend } from '../components/map/MapLegend';
import { ParcelInspector } from '../components/map/ParcelInspector';
import { AIInsightsPanel } from '../components/map/AIInsightsPanel';
import { ReviewQueue } from '../components/review/ReviewQueue';
import { BoundaryEditor } from '../components/editing/BoundaryEditor';
import { AnalyticsDrawer } from '../components/analytics/AnalyticsDrawer';
import { GlowingButton } from '../components/common/GlowingButton';
import { SpatialDataIngestion } from '../components/ingestion/SpatialDataIngestion';
import { 
  Sparkles, 
  CheckSquare, 
  History, 
  FileText, 
  BarChart3, 
  Layers,
  MapPin,
  Maximize2,
  Minimize2
} from 'lucide-react';

export function DashboardPage() {
  const navigate = useNavigate();
  const { mapInstance } = useMapSelection();
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);
  const [mapMaximized, setMapMaximized] = useState(false);

  useEffect(() => {
    if (!mapInstance) return;
    const frame = window.requestAnimationFrame(() => mapInstance.resize());
    return () => window.cancelAnimationFrame(frame);
  }, [mapInstance, mapMaximized]);

  return (
    <div className="relative h-full w-full overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(167,235,242,0.28),transparent_18%),linear-gradient(180deg,#effbfe_0%,#eaf8fb_100%)] p-3 lg:p-4">
      <div className="relative grid h-full grid-cols-12 gap-3 lg:gap-4">
        <div className={`col-span-12 flex max-h-full flex-col space-y-3 overflow-y-auto lg:col-span-3 lg:space-y-4 ${mapMaximized ? 'hidden' : ''}`}>
          <div className="cv-panel-elevated flex shrink-0 items-center justify-between rounded-2xl p-3.5 transition-all duration-200 hover:-translate-y-0.5">
            <div className="flex items-center space-x-2.5">
              <div className="rounded-xl bg-[linear-gradient(135deg,rgba(167,235,242,0.5),rgba(84,172,191,0.2))] p-2 text-[#023859]">
                <Layers className="h-4 w-4" />
              </div>
              <div>
                <h2 className="font-display text-xs font-bold uppercase tracking-[0.18em] text-[#011C40]">COMMAND CENTER</h2>
                <p className="font-mono text-[10px] text-[#4F7285]">Sector 4 • Interactive GIS</p>
              </div>
            </div>
            <button
              onClick={() => setIsAnalyticsOpen(true)}
              className="flex items-center space-x-1 rounded-lg border border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(247,252,254,0.95),rgba(220,244,250,0.9))] p-1.5 text-xs font-semibold text-[#266580] transition-all duration-200 hover:-translate-y-0.5 hover:border-[#54ACBF] hover:shadow-[0_8px_20px_rgba(2,56,89,0.08)]"
              title="Open Cadastral Analytics Drawer"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              <span className="hidden text-[11px] xl:inline">Stats</span>
            </button>
          </div>

          <SpatialDataIngestion />
          <LayerControl />
          <MapLegend />
        </div>

        <div id="gis-map-panel" className={`col-span-12 flex max-h-full flex-col space-y-3 overflow-hidden lg:col-span-6 lg:space-y-4 ${mapMaximized ? 'cv-map-panel-maximized absolute inset-0 z-30 p-0' : ''}`}>
          <div className="cv-panel-elevated flex shrink-0 items-center justify-between gap-2 overflow-x-auto rounded-2xl p-2 px-3">
            <span className="flex shrink-0 items-center space-x-1 text-[11px] font-bold uppercase tracking-[0.18em] text-[#4F7285] font-mono">
              <MapPin className="h-3 w-3 text-[#266580]" />
              <span>Quick Actions</span>
            </span>

            <div className="flex shrink-0 items-center space-x-2">
              <GlowingButton
                variant="primary-glow"
                size="sm"
                icon={Sparkles}
                onClick={() => navigate('/ai-analysis')}
              >
                Analyze Area
              </GlowingButton>

              <GlowingButton
                variant="secondary-pastel"
                size="sm"
                icon={CheckSquare}
                onClick={() => navigate('/review')}
              >
                Review Parcels
              </GlowingButton>

              <GlowingButton
                variant="secondary-pastel"
                size="sm"
                icon={History}
                onClick={() => navigate('/history')}
              >
                View History
              </GlowingButton>

              <GlowingButton
                variant="accent"
                size="sm"
                icon={FileText}
                onClick={() => navigate('/reports')}
              >
                Reports
              </GlowingButton>
            </div>
          </div>

          <div className="relative min-h-[350px] flex-1 overflow-hidden rounded-[22px] border border-[#A7EBF2]/70 bg-[linear-gradient(180deg,rgba(1,28,64,0.96),rgba(2,56,89,0.8))] p-[1px] shadow-[0_20px_40px_rgba(1,28,64,0.16)]">
            <div className="h-full w-full overflow-hidden rounded-[21px] border border-[#54ACBF]/35 bg-[#011C40]">
              <MapView />
            </div>
            <button
              type="button"
              onClick={() => setMapMaximized((maximized) => !maximized)}
              className="cv-map-maximize-button"
              aria-label={mapMaximized ? 'Restore map' : 'Maximize map'}
              title={mapMaximized ? 'Restore map' : 'Maximize map'}
            >
              {mapMaximized ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </button>
          </div>

          <div className={`h-auto shrink-0 ${mapMaximized ? 'hidden' : ''}`}>
            <ReviewQueue />
          </div>
        </div>

        <div className={`col-span-12 flex max-h-full flex-col space-y-3 overflow-y-auto lg:col-span-3 lg:space-y-4 ${mapMaximized ? 'hidden' : ''}`}>
          <div className="min-h-[280px] flex-1">
            <ParcelInspector />
          </div>
          <div>
            <AIInsightsPanel />
          </div>
        </div>
      </div>

      <BoundaryEditor />
      <AnalyticsDrawer isOpen={isAnalyticsOpen} onClose={() => setIsAnalyticsOpen(false)} />
    </div>
  );
}
