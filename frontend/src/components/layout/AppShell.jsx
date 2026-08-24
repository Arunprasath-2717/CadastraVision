import React, { useState } from 'react';
import { TopBar } from './TopBar';
import { MapView } from '../map/MapView';
import { LayerControl } from '../map/LayerControl';
import { MapLegend } from '../map/MapLegend';
import { ParcelInspector } from '../map/ParcelInspector';
import { AIInsightsPanel } from '../map/AIInsightsPanel';
import { ReviewQueue } from '../review/ReviewQueue';
import { BoundaryEditor } from '../editing/BoundaryEditor';
import { AnalyticsDrawer } from '../analytics/AnalyticsDrawer';

export function AppShell() {
  const [isAnalyticsOpen, setIsAnalyticsOpen] = useState(false);

  return (
    <div className="h-screen w-screen bg-pastel-bg overflow-hidden flex flex-col font-sans text-pastel-text">
      
      {/* Top Bar Header */}
      <TopBar onToggleAnalytics={() => setIsAnalyticsOpen(!isAnalyticsOpen)} />

      {/* Main Workstation Command Center Grid */}
      <div className="flex-1 p-4 grid grid-cols-12 gap-4 overflow-hidden relative">
        
        {/* Left Column — Layer Explorer & Legend (3 cols) */}
        <div className="col-span-12 lg:col-span-3 flex flex-col space-y-4 overflow-y-auto max-h-full">
          <LayerControl />
          <MapLegend />
        </div>

        {/* Central Map & Review Queue Column (6 cols) */}
        <div className="col-span-12 lg:col-span-6 flex flex-col space-y-4 max-h-full overflow-hidden">
          {/* Map Container */}
          <div className="flex-1 relative overflow-hidden min-h-[350px]">
            <MapView />
          </div>

          {/* Bottom Review Queue */}
          <div className="h-auto">
            <ReviewQueue />
          </div>
        </div>

        {/* Right Column — Inspector & AI Insights (3 cols) */}
        <div className="col-span-12 lg:col-span-3 flex flex-col space-y-4 max-h-full overflow-y-auto">
          <div className="flex-1 min-h-[280px]">
            <ParcelInspector />
          </div>
          <div>
            <AIInsightsPanel />
          </div>
        </div>

        {/* Boundary Editor Floating Modal */}
        <BoundaryEditor />

        {/* Cadastral Analytics Drawer */}
        <AnalyticsDrawer isOpen={isAnalyticsOpen} onClose={() => setIsAnalyticsOpen(false)} />

      </div>

    </div>
  );
}
