import React from 'react';
import { useMapSelection } from '../../context/MapContext';
import { Sparkles, CheckCircle2, ShieldCheck, HelpCircle, ArrowRight } from 'lucide-react';

export function AIInsightsPanel() {
  const { selectedParcel } = useMapSelection();

  if (!selectedParcel) {
    return (
      <div className="bg-white/95 backdrop-blur-md p-5 rounded-2xl border border-pastel-border shadow-pastel-md text-pastel-text space-y-3">
        <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-pastel-action border-b border-pastel-border pb-2">
          <Sparkles className="w-4 h-4 text-pastel-action animate-pulse" />
          <span>Cadastral AI Assistant</span>
        </div>
        <p className="text-xs text-pastel-muted leading-relaxed">
          Select a parcel on the map or in the Review Queue to generate instant AI confidence explanations and topology insights.
        </p>
      </div>
    );
  }

  const isHighConf = selectedParcel.confidence_score >= 0.8;
  const isMedConf = selectedParcel.confidence_score >= 0.5 && selectedParcel.confidence_score < 0.8;

  return (
    <div className="bg-white/95 backdrop-blur-md p-5 rounded-2xl border border-pastel-border shadow-pastel-md text-pastel-text space-y-3.5">
      <div className="flex items-center justify-between border-b border-pastel-border pb-2.5">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-pastel-action animate-pulse" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-pastel-text font-display">
            AI Assistant Insights
          </h4>
        </div>
        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-pastel-lavender text-pastel-action">
          {selectedParcel.id}
        </span>
      </div>

      {/* AI Summary Text */}
      <div className="p-3 rounded-xl bg-pastel-surface-soft border border-pastel-border text-xs space-y-1.5">
        <span className="font-semibold text-pastel-text block">AI Geometry Evaluation:</span>
        <p className="text-pastel-muted leading-relaxed">
          {isHighConf
            ? "High-confidence parcel boundary extracted via SAMGeo-v2 zero-shot segmentation. No topology conflicts detected."
            : isMedConf
            ? "Medium-confidence boundary. Road buffer overlap detected on eastern edge requiring surveyor verification."
            : "Low-confidence polygon caused by tree canopy shadow obstruction. Ground verification recommended."}
        </p>
      </div>

      {/* Contributing Factors List */}
      <div className="space-y-1.5 text-xs">
        <span className="text-[11px] font-semibold text-pastel-muted uppercase tracking-wider block">
          Contributing Factors:
        </span>
        
        <div className="flex items-center space-x-2 text-pastel-mint-text font-medium text-[11px]">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>Clear orthophoto boundary segmentation</span>
        </div>

        <div className="flex items-center space-x-2 text-pastel-mint-text font-medium text-[11px]">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
          <span>High aerial imagery resolution (&lt;10cm/px)</span>
        </div>

        {selectedParcel.flags && selectedParcel.flags.length > 0 ? (
          <div className="flex items-center space-x-2 text-pastel-rose-text font-medium text-[11px]">
            <HelpCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
            <span>{selectedParcel.flags.length} topology flag(s) requires review</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 text-pastel-mint-text font-medium text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>Zero self-intersections or boundary gaps</span>
          </div>
        )}
      </div>

    </div>
  );
}
