import React from 'react';
import { Link } from 'react-router-dom';
import { LandingHeader } from '../components/landing/LandingHeader';
import { InteractiveHeroText } from '../components/landing/InteractiveHeroText';
import { Map, Shield, ArrowRight, Activity, Sparkles, CheckCircle2 } from 'lucide-react';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-pastel-bg text-pastel-text topo-grid-pastel relative overflow-hidden flex flex-col justify-between">
      <LandingHeader />

      {/* Hero Section */}
      <main className="pt-32 pb-20 px-6 max-w-7xl mx-auto flex-1 flex flex-col justify-center items-center text-center relative z-10">
        {/* Top Metadata Pill */}
        <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-pastel-lavender border border-pastel-border text-xs font-semibold text-pastel-action mb-8 shadow-pastel-sm">
          <Sparkles className="w-3.5 h-3.5 text-pastel-action animate-pulse" />
          <span>AI-Assisted Automated Urban Cadastral Mapping</span>
        </div>

        {/* Interactive Main Hero Title (Preserving cursor repulsion) */}
        <div className="w-full max-w-5xl">
          <InteractiveHeroText text="AI-POWERED CADASTRAL INTELLIGENCE" />
        </div>

        {/* Supporting Hero Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-pastel-muted max-w-3xl font-normal leading-relaxed">
          Transform aerial imagery into accurate, validated and GIS-ready urban parcel information.
        </p>

        <p className="mt-2 text-xs text-pastel-subtle tracking-widest font-mono uppercase">
          Map. Validate. Review. Approve.
        </p>

        {/* Main CTA */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to="/dashboard"
            className="w-full sm:w-auto px-8 py-4 rounded-xl bg-pastel-action hover:bg-pastel-action-hover text-white font-semibold text-base shadow-pastel-md hover:shadow-pastel-lg transition-all duration-300 flex items-center justify-center space-x-3 border border-blue-400/30 group"
          >
            <span>Enter GIS Workstation</span>
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>

          <Link
            to="/login"
            className="w-full sm:w-auto px-7 py-4 rounded-xl bg-white hover:bg-slate-50 text-pastel-text font-medium text-base transition-all duration-300 border border-pastel-border shadow-pastel-sm flex items-center justify-center"
          >
            <span>Staff Login</span>
          </Link>
        </div>

        {/* Trust Cards */}
        <div className="mt-16 pt-8 border-t border-pastel-border/80 w-full max-w-4xl grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="pastel-card p-5 rounded-2xl text-left border border-pastel-border shadow-pastel-sm flex items-start space-x-3">
            <div className="p-2.5 bg-blue-50 text-pastel-action rounded-xl">
              <Map className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-pastel-text">AI Boundary Extraction</h3>
              <p className="text-xs text-pastel-muted mt-1">SAMGeo & YOLOv8 instance segmentation of drone GeoTIFF imagery.</p>
            </div>
          </div>

          <div className="pastel-card p-5 rounded-2xl text-left border border-pastel-border shadow-pastel-sm flex items-start space-x-3">
            <div className="p-2.5 bg-amber-50 text-amber-600 rounded-xl">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-pastel-text">Topology Validation</h3>
              <p className="text-xs text-pastel-muted mt-1">Automatic overlap, gap, and self-intersection flag detection.</p>
            </div>
          </div>

          <div className="pastel-card p-5 rounded-2xl text-left border border-pastel-border shadow-pastel-sm flex items-start space-x-3">
            <div className="p-2.5 bg-emerald-50 text-emerald-600 rounded-xl">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-pastel-text">Human Approval Workflow</h3>
              <p className="text-xs text-pastel-muted mt-1">Surveyor review queue, vertex drag editing, and audit trail.</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer Metadata */}
      <footer className="py-6 border-t border-pastel-border bg-white text-center text-xs text-pastel-muted relative z-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
            <span className="font-mono text-pastel-text font-medium">AI-assisted • GIS-ready • Human-validated</span>
          </div>
          <div>
            Ministry of Rural Development — Smart India Hackathon 2026 (PS 26012)
          </div>
        </div>
      </footer>
    </div>
  );
}
