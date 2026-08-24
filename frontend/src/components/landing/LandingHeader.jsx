import React from 'react';
import { Link } from 'react-router-dom';
import { Layers, ShieldCheck } from 'lucide-react';

export function LandingHeader() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-pastel-border px-6 py-4 shadow-pastel-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo & Name */}
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-xl bg-pastel-lavender border border-pastel-border flex items-center justify-center text-pastel-action group-hover:border-pastel-action transition-all duration-300">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-wider text-pastel-text font-display">CADASTRALMAP</span>
            <div className="flex items-center space-x-1.5 text-[10px] text-pastel-muted tracking-widest uppercase">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              <span>SIH 2026 • MoRD Platform</span>
            </div>
          </div>
        </Link>

        {/* Action Controls */}
        <div className="flex items-center space-x-4">
          <Link
            to="/login"
            className="px-4 py-2 text-sm font-medium text-pastel-muted hover:text-pastel-text transition-colors duration-200"
          >
            Sign In
          </Link>
          <Link
            to="/dashboard"
            className="px-5 py-2 text-sm font-semibold text-white bg-pastel-action hover:bg-pastel-action-hover rounded-xl shadow-pastel-md hover:shadow-pastel-lg transition-all duration-300 flex items-center space-x-2 border border-blue-400/30"
          >
            <span>Enter Workspace</span>
          </Link>
        </div>
      </div>
    </header>
  );
}
