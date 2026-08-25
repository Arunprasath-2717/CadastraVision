import React from 'react';
import { Link } from 'react-router-dom';
import { LandingHeader } from '../components/landing/LandingHeader';
import { InteractiveHeroText } from '../components/landing/InteractiveHeroText';
import { Map, Shield, ArrowRight, Activity, Sparkles, CheckCircle2 } from 'lucide-react';

export function LandingPage() {
  return (
    <div className="relative flex min-h-screen flex-col justify-between overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(167,235,242,0.42),transparent_22%),radial-gradient(circle_at_bottom_right,rgba(84,172,191,0.18),transparent_20%),linear-gradient(180deg,#eefbff_0%,#eaf8fb_100%)] text-pastel-text topo-grid-pastel">
      <LandingHeader />

      <main className="relative z-10 mx-auto flex max-w-7xl flex-1 flex-col items-center justify-center px-6 pb-20 pt-32 text-center">
        <div className="mb-8 inline-flex items-center space-x-2 rounded-full border border-[#A7EBF2] bg-[linear-gradient(135deg,rgba(167,235,242,0.20),rgba(255,255,255,0.90))] px-4 py-1.5 text-xs font-semibold text-[#023859] shadow-[0_10px_24px_rgba(2,56,89,0.08)]">
          <Sparkles className="h-3.5 w-3.5 animate-pulse text-[#266580]" />
          <span>AI-Assisted Automated Urban Cadastral Mapping</span>
        </div>

        <div className="w-full max-w-5xl">
          <InteractiveHeroText text="AI-POWERED CADASTRAL INTELLIGENCE" />
        </div>

        <p className="mt-6 max-w-3xl text-lg font-normal leading-relaxed text-[#4F7285] sm:text-xl">
          Transform aerial imagery into accurate, validated and GIS-ready urban parcel information.
        </p>

        <p className="mt-2 font-mono text-xs uppercase tracking-[0.22em] text-[#6F8DA0]">
          Map. Validate. Review. Approve.
        </p>

        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            to="/dashboard"
            className="group flex w-full items-center justify-center space-x-3 rounded-xl border border-[#54ACBF]/30 bg-[linear-gradient(135deg,#011C40,#023859)] px-8 py-4 text-base font-semibold text-white shadow-[0_16px_30px_rgba(1,28,64,0.18)] transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_18px_36px_rgba(2,56,89,0.22)] sm:w-auto"
          >
            <span>Enter GIS Workstation</span>
            <ArrowRight className="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" />
          </Link>

          <Link
            to="/login"
            className="flex w-full items-center justify-center rounded-xl border border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(239,249,251,0.88))] px-7 py-4 text-base font-medium text-[#011C40] shadow-[0_8px_20px_rgba(2,56,89,0.06)] transition-all duration-300 hover:-translate-y-0.5 hover:border-[#54ACBF] sm:w-auto"
          >
            <span>Staff Login</span>
          </Link>
        </div>

        <div className="mt-16 grid w-full max-w-4xl grid-cols-1 gap-6 border-t border-[#C9E5EE]/80 pt-8 md:grid-cols-3">
          <div className="pastel-card flex items-start space-x-3 rounded-2xl border border-[#C9E5EE] p-5 text-left shadow-[0_12px_28px_rgba(1,28,64,0.08)] transition-all duration-200 hover:-translate-y-1 hover:border-[#54ACBF] hover:shadow-[0_16px_34px_rgba(2,56,89,0.12)]">
            <div className="rounded-xl bg-[linear-gradient(135deg,rgba(167,235,242,0.35),rgba(84,172,191,0.18))] p-2.5 text-[#266580]">
              <Map className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#011C40]">AI Boundary Extraction</h3>
              <p className="mt-1 text-xs leading-relaxed text-[#4F7285]">SAMGeo & YOLOv8 instance segmentation of drone GeoTIFF imagery.</p>
            </div>
          </div>

          <div className="pastel-card flex items-start space-x-3 rounded-2xl border border-[#C9E5EE] p-5 text-left shadow-[0_12px_28px_rgba(1,28,64,0.08)] transition-all duration-200 hover:-translate-y-1 hover:border-[#54ACBF] hover:shadow-[0_16px_34px_rgba(2,56,89,0.12)]">
            <div className="rounded-xl bg-[linear-gradient(135deg,rgba(246,215,166,0.35),rgba(255,255,255,0.7))] p-2.5 text-amber-600">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#011C40]">Topology Validation</h3>
              <p className="mt-1 text-xs leading-relaxed text-[#4F7285]">Automatic overlap, gap, and self-intersection flag detection.</p>
            </div>
          </div>

          <div className="pastel-card flex items-start space-x-3 rounded-2xl border border-[#C9E5EE] p-5 text-left shadow-[0_12px_28px_rgba(1,28,64,0.08)] transition-all duration-200 hover:-translate-y-1 hover:border-[#54ACBF] hover:shadow-[0_16px_34px_rgba(2,56,89,0.12)]">
            <div className="rounded-xl bg-[linear-gradient(135deg,rgba(167,235,242,0.28),rgba(16,185,129,0.12))] p-2.5 text-emerald-600">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-[#011C40]">Human Approval Workflow</h3>
              <p className="mt-1 text-xs leading-relaxed text-[#4F7285]">Surveyor review queue, vertex drag editing, and audit trail.</p>
            </div>
          </div>
        </div>
      </main>

      <footer className="relative z-10 border-t border-[#C9E5EE] bg-[linear-gradient(180deg,rgba(255,255,255,0.82),rgba(229,246,252,0.9))] py-6 text-center text-xs text-[#4F7285]">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <div className="flex items-center space-x-2">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
            <span className="font-mono font-medium text-[#011C40]">AI-assisted • GIS-ready • Human-validated</span>
          </div>
          <div>
            Ministry of Rural Development — Smart India Hackathon 2026 (PS 26012)
          </div>
        </div>
      </footer>
    </div>
  );
}
