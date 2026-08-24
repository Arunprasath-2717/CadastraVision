import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMapSelection } from '../context/MapContext';
import { GlowingButton } from '../components/common/GlowingButton';
import { 
  Sparkles, 
  Send, 
  MapPin, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Info, 
  ArrowRight, 
  Bot, 
  FileText, 
  Layers, 
  BarChart3,
  ExternalLink,
  History
} from 'lucide-react';

export function AISpatialPage() {
  const navigate = useNavigate();
  const { selectParcel } = useMapSelection();

  const [queryInput, setQueryInput] = useState('');
  const [activeQuery, setActiveQuery] = useState('Show parcels with boundary anomalies in Sector 4');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const suggestedPrompts = [
    "Show parcels with boundary anomalies",
    "Identify overlapping building footprints",
    "Detect unverified land-use changes",
    "Find high-risk cadastral discrepancies",
    "Summarize GIS validation score for Sector 4",
  ];

  const analysisHistory = [
    { text: "Show parcels with boundary anomalies", date: "10 mins ago", count: 128 },
    { text: "Find high-risk cadastral discrepancies", date: "1 hour ago", count: 42 },
    { text: "Identify overlapping building footprints", date: "3 hours ago", count: 15 },
  ];

  const anomalyResults = [
    {
      id: 'P-1024',
      title: 'Overlap Discrepancy detected',
      risk: 'High',
      confidence: 0.94,
      affectedArea: '142 m²',
      description: 'Polygon boundary overlaps adjacent municipal road right-of-way by 1.8 meters along Eastern edge.',
      recommendation: 'Adjust vertex 3 & 4 to realign with satellite edge line.',
      zone: 'Sector 4 • Residential'
    },
    {
      id: 'P-1025',
      title: 'Unverified Building Expansion',
      risk: 'Medium',
      confidence: 0.88,
      affectedArea: '85 m²',
      description: 'Building footprint exceeds registered parcel geometry boundary by 4.2% based on latest ortho-mosaic scan.',
      recommendation: 'Flag for surveyor ground verification.',
      zone: 'Sector 4 • Mixed Commercial'
    },
    {
      id: 'P-1026',
      title: 'Gap Anomaly between parcels',
      risk: 'Low',
      confidence: 0.96,
      affectedArea: '18 m²',
      description: 'Unmapped spatial gap between parcel P-1026 and P-1027 violates topological continuity.',
      recommendation: 'Auto-snap shared boundary edge.',
      zone: 'Sector 4 • Residential'
    },
    {
      id: 'P-1027',
      title: 'Land-Use Classification Variance',
      risk: 'Medium',
      confidence: 0.82,
      affectedArea: '310 m²',
      description: 'Deed lists agricultural status, but thermal satellite imagery indicates active industrial warehousing.',
      recommendation: 'Update tax assessment record to Commercial.',
      zone: 'Sector 4 • Special Economic Zone'
    }
  ];

  const handleQuerySubmit = (e) => {
    e.preventDefault();
    if (!queryInput.trim()) return;
    setActiveQuery(queryInput);
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
    }, 800);
  };

  const handleSelectPrompt = (promptText) => {
    setQueryInput(promptText);
    setActiveQuery(promptText);
    setIsAnalyzing(true);
    setTimeout(() => {
      setIsAnalyzing(false);
    }, 600);
  };

  const handleViewOnMap = (parcelId) => {
    selectParcel(parcelId, true);
    navigate('/dashboard');
  };

  return (
    <div className="h-full w-full p-4 lg:p-6 overflow-y-auto bg-pastel-bg space-y-6">
      
      {/* Workspace Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 lg:p-8 rounded-3xl border border-indigo-900/40 shadow-2xl relative overflow-hidden">
        {/* Neon Glow Backdrop Effect */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-cyan-500/20 via-sky-500/10 to-transparent blur-3xl pointer-events-none" />
        
        <div className="relative z-10 max-w-4xl space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-sky-500/20 border border-sky-400/30 text-sky-300 text-xs font-mono font-medium">
            <Sparkles className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
            <span>AI SPATIAL INTELLIGENCE COPILOT</span>
          </div>

          <h1 className="text-2xl lg:text-3xl font-extrabold font-display tracking-tight text-white">
            Ask Your Cadastral Map
          </h1>

          <p className="text-xs lg:text-sm text-slate-300 max-w-2xl leading-relaxed">
            Execute natural language spatial queries, perform real-time boundary anomaly detection, and evaluate machine learning confidence scores across sector GIS layers.
          </p>

          {/* Prompt Search Input */}
          <form onSubmit={handleQuerySubmit} className="pt-2 flex items-center max-w-2xl">
            <div className="relative w-full">
              <input
                type="text"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="e.g. 'Show parcels with boundary anomalies in Sector 4'..."
                className="w-full pl-11 pr-32 py-3 bg-slate-800/90 border border-indigo-500/40 rounded-2xl text-xs lg:text-sm text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-400 shadow-xl"
              />
              <Bot className="w-5 h-5 text-sky-400 absolute left-3.5 top-3.5" />
              <div className="absolute right-2 top-2">
                <GlowingButton
                  type="submit"
                  variant="primary-glow"
                  size="sm"
                  icon={Send}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Execute'}
                </GlowingButton>
              </div>
            </div>
          </form>

          {/* Suggested Prompts */}
          <div className="pt-2 flex items-center space-x-2 overflow-x-auto text-xs">
            <span className="text-slate-400 font-mono text-[11px] shrink-0">Try:</span>
            {suggestedPrompts.map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSelectPrompt(prompt)}
                className="px-3 py-1 rounded-xl bg-slate-800/70 hover:bg-slate-700/90 text-sky-200 border border-slate-700/60 transition-colors shrink-0 text-[11px] font-medium"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Query Summary & Risk Breakdown Grid */}
      <div className="grid grid-cols-12 gap-4 lg:gap-6">
        
        {/* Stats & Confidence Cards (4 cols) */}
        <div className="col-span-12 lg:col-span-4 space-y-4">
          
          {/* Active Query Card */}
          <div className="bg-white p-5 rounded-2xl border border-pastel-border shadow-pastel-sm space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-pastel-muted font-mono">
                CURRENT QUERY ANALYSIS
              </span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold font-mono text-[11px]">
                94% Confidence
              </span>
            </div>

            <p className="text-sm font-semibold text-pastel-text bg-pastel-surface-soft p-3 rounded-xl border border-pastel-border">
              "{activeQuery}"
            </p>

            <div className="pt-2 border-t border-pastel-border grid grid-cols-2 gap-3 text-center">
              <div className="p-3 bg-pastel-lavender/60 rounded-xl border border-pastel-border">
                <span className="block text-xl font-bold font-mono text-pastel-action">128</span>
                <span className="text-[10px] text-pastel-muted uppercase tracking-wider font-mono">Parcels Scanned</span>
              </div>
              <div className="p-3 bg-amber-50 rounded-xl border border-amber-200">
                <span className="block text-xl font-bold font-mono text-amber-800">42</span>
                <span className="text-[10px] text-amber-700 uppercase tracking-wider font-mono">Flagged Anomalies</span>
              </div>
            </div>
          </div>

          {/* Risk Level Distribution Breakdown */}
          <div className="bg-white p-5 rounded-2xl border border-pastel-border shadow-pastel-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-pastel-muted font-mono flex items-center space-x-1.5">
              <BarChart3 className="w-4 h-4 text-pastel-action" />
              <span>RISK DISTRIBUTION SCORE</span>
            </h3>

            <div className="space-y-3">
              {/* High Risk */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-rose-700 flex items-center space-x-1">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>High Risk</span>
                  </span>
                  <span className="font-mono text-rose-800">42 parcels (33%)</span>
                </div>
                <div className="w-full h-2.5 bg-rose-100 rounded-full overflow-hidden">
                  <div className="h-full bg-rose-500 rounded-full" style={{ width: '33%' }} />
                </div>
              </div>

              {/* Medium Risk */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-amber-700 flex items-center space-x-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Medium Risk</span>
                  </span>
                  <span className="font-mono text-amber-800">56 parcels (44%)</span>
                </div>
                <div className="w-full h-2.5 bg-amber-100 rounded-full overflow-hidden">
                  <div className="h-full bg-amber-500 rounded-full" style={{ width: '44%' }} />
                </div>
              </div>

              {/* Low Risk */}
              <div>
                <div className="flex justify-between text-xs font-semibold mb-1">
                  <span className="text-emerald-700 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Low Risk</span>
                  </span>
                  <span className="font-mono text-emerald-800">30 parcels (23%)</span>
                </div>
                <div className="w-full h-2.5 bg-emerald-100 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: '23%' }} />
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-pastel-border flex justify-between items-center text-xs">
              <span className="text-pastel-muted">Actionable Items:</span>
              <GlowingButton
                variant="secondary-pastel"
                size="sm"
                icon={ExternalLink}
                onClick={() => navigate('/review')}
              >
                Go to Review Queue
              </GlowingButton>
            </div>
          </div>

          {/* AI Analysis History */}
          <div className="bg-white p-5 rounded-2xl border border-pastel-border shadow-pastel-sm space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-pastel-muted font-mono flex items-center space-x-1.5">
              <History className="w-4 h-4 text-pastel-action" />
              <span>RECENT AI QUERIES</span>
            </h3>

            <div className="space-y-2">
              {analysisHistory.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectPrompt(item.text)}
                  className="w-full text-left p-3 rounded-xl bg-pastel-surface-soft hover:bg-pastel-lavender transition-colors border border-pastel-border text-xs flex justify-between items-center group"
                >
                  <div>
                    <p className="font-medium text-pastel-text group-hover:text-pastel-action transition-colors">{item.text}</p>
                    <p className="text-[10px] text-pastel-muted font-mono">{item.date}</p>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-white font-mono text-[10px] font-bold text-pastel-action border border-pastel-border">
                    {item.count}
                  </span>
                </button>
              ))}
            </div>
          </div>

        </div>

        {/* Affected Parcels & AI Explanation Cards (8 cols) */}
        <div className="col-span-12 lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-pastel-text font-mono flex items-center space-x-2">
              <Layers className="w-4 h-4 text-pastel-action" />
              <span>DETECTED SPATIAL ANOMALIES ({anomalyResults.length})</span>
            </h2>
            <span className="text-xs text-pastel-muted font-mono">Sorted by severity</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {anomalyResults.map((item) => (
              <div
                key={item.id}
                className="bg-white p-5 rounded-2xl border border-pastel-border shadow-pastel-sm hover:shadow-pastel-md transition-all space-y-3 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm font-mono text-pastel-text">{item.id}</span>
                    <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-mono uppercase font-bold ${
                      item.risk === 'High'
                        ? 'bg-rose-100 text-rose-800 border border-rose-300'
                        : item.risk === 'Medium'
                        ? 'bg-amber-100 text-amber-800 border border-amber-300'
                        : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    }`}>
                      {item.risk} Risk
                    </span>
                  </div>

                  <h3 className="font-bold text-xs text-pastel-text">{item.title}</h3>
                  <p className="text-xs text-pastel-muted leading-relaxed">{item.description}</p>

                  <div className="p-3 rounded-xl bg-pastel-lavender/60 border border-pastel-border text-xs space-y-1">
                    <div className="flex items-center space-x-1 text-[11px] font-semibold text-pastel-action">
                      <Info className="w-3.5 h-3.5 shrink-0" />
                      <span>AI RATIONALE & RECOMMENDATION</span>
                    </div>
                    <p className="text-[11px] text-pastel-text">{item.recommendation}</p>
                  </div>
                </div>

                <div className="pt-3 border-t border-pastel-border flex items-center justify-between text-xs">
                  <div className="text-[11px] text-pastel-muted font-mono">
                    <span>Conf: {(item.confidence * 100).toFixed(0)}%</span>
                    <span className="mx-1.5">•</span>
                    <span>Area: {item.affectedArea}</span>
                  </div>

                  <GlowingButton
                    variant="primary-glow"
                    size="sm"
                    icon={MapPin}
                    onClick={() => handleViewOnMap(item.id)}
                  >
                    View on Map
                  </GlowingButton>
                </div>
              </div>
            ))}
          </div>

          {/* AI Spatial Report Summary Box */}
          <div className="bg-gradient-to-br from-pastel-lavender to-sky-50 p-6 rounded-2xl border border-pastel-border shadow-pastel-sm space-y-3">
            <div className="flex items-center space-x-2 text-pastel-action font-bold text-xs font-mono uppercase tracking-wider">
              <FileText className="w-4 h-4" />
              <span>AI CADASTRAL INSIGHT SUMMARY</span>
            </div>
            <p className="text-xs text-pastel-text leading-relaxed">
              Spatial intelligence clustering indicates 33% of anomalies in Sector 4 are concentrated near the eastern right-of-way corridor due to 2019 satellite registration offset. Running automatic boundary realignment is recommended prior to final tax roll generation.
            </p>
            <div className="pt-2 flex items-center space-x-3">
              <GlowingButton
                variant="secondary-pastel"
                size="sm"
                icon={ArrowRight}
                onClick={() => navigate('/reports')}
              >
                Generate Full AI Report
              </GlowingButton>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
